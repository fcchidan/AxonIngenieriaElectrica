from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from blog.models import Categoria, Producto, ElementoCarrito, Orden, DireccionEnvio, ElementoOrden
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from mainapp.forms import RegisterForm, DireccionEnvioForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.conf import settings
from django.template.loader import render_to_string, get_template
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives, send_mail, EmailMessage

# Create your views here.
def index(request):
    return render(request, 'index.html')


def productos(request):
    
    productos = Producto.objects.all()
    paginator = Paginator(productos, 3)
    
    page = request.GET.get('page')
    page_productos = paginator.get_page(page)
    
    
    return render(request, 'productos.html',{
        'productos': page_productos
    })

def clientes(request):
    return render(request, 'clientes.html')

def contacto(request):
    return render(request, 'contacto.html')

def empresa(request):
    return render(request, 'empresa.html')

def representacion(request):
    return render(request, 'representacion.html')

def servicios(request):
    return render(request, 'servicios.html')




def categoria(request, categoria_id):
    categoria = Categoria.objects.get(id=categoria_id)
    productos = Producto.objects.filter(categorias=categoria_id)
    
    return render(request, 'categorias.html',{
        'categoria': categoria,
        'productos': productos
    })
    

def producto(request, producto_id):
    
    producto = Producto.objects.get(id=producto_id)
    
    return render(request, 'producto.html',{
        'producto' : producto
    })
    

def register_page(request):

    registro_form = RegisterForm()

    if request.method == 'POST':
        registro_form = RegisterForm(request.POST)

        if registro_form.is_valid():
            registro_form.save()
            messages.success(request, 'Te has registrado correctamente!!')

            return redirect('inicio')

    return render(request, 'registro.html',{
        'title': 'Registro',
        'registro_form': registro_form
    })


def login_page(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    else:

        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('inicio')
            else:
                messages.warning(request, 'No te has podido identificado correctamente')

        return render(request, 'login.html',{
            'title': 'Registrate'
        })

def logout_user(request):
    logout(request)
    return redirect('login')

#------------------------------------------------------------------------------------

@login_required
def ver_carrito(request):
    elementos_carrito = ElementoCarrito.objects.filter(usuario=request.user)
    total_carrito = sum(item.subtotal() for item in elementos_carrito)
    total_productos_carrito = sum(item.cantidad for item in elementos_carrito)
    cantidad_productos_carrito = elementos_carrito.count()
    return render(request, 'carrito.html', {'elementos_carrito': elementos_carrito, 'total_carrito': total_carrito, 'cantidad_productos_carrito': cantidad_productos_carrito, 'total_productos_carrito': total_productos_carrito})

@login_required
def agregar_al_carrito(request, producto_id):
    producto = Producto.objects.get(pk=producto_id)
    elemento, created = ElementoCarrito.objects.get_or_create(usuario=request.user, producto=producto)
    if not created:
        elemento.cantidad += 1
        elemento.save()
    return redirect(request.META.get('HTTP_REFERER','ver_carrito'))
"""
@login_required
def eliminar_del_carrito(request, elemento_id):
    elemento = ElementoCarrito.objects.get(pk=elemento_id)
    if elemento.usuario == request.user:
        elemento.delete()
    return redirect('ver_carrito')
"""


@login_required
def eliminar_del_carrito(request, elemento_id):
    elemento = ElementoCarrito.objects.get(pk=elemento_id)
    if elemento.usuario == request.user:
        elemento.delete()
    return redirect('ver_carrito')

@login_required
def vaciar_carrito(request):
    ElementoCarrito.objects.filter(usuario=request.user).delete()
    return redirect('ver_carrito')

@login_required
def realizar_orden(request):
    if request.method == 'POST':
        form = DireccionEnvioForm(request.POST)
        if form.is_valid():
            direccion_envio = form.save()  # Guardar la dirección de envío

            # Calcular el precio total de los elementos en el carrito
            elementos_carrito = ElementoCarrito.objects.filter(usuario=request.user)
            precio_total = sum(elemento.subtotal() for elemento in elementos_carrito)
            
            # Crear la orden y asignar el precio total y la dirección de envío
            orden = Orden.objects.create(
                usuario=request.user,
                precio_total=precio_total,
                direccion_envio=direccion_envio
            )
            
            # Crear los elementos de la orden basados en el carrito
            for elemento in elementos_carrito:
                ElementoOrden.objects.create(
                    orden=orden,
                    producto=elemento.producto,
                    cantidad=elemento.cantidad
                )
            
            # Limpiar el carrito después de realizar la orden
            elementos_carrito.delete()
            
            return redirect('ver_carrito')
    else:
        form = DireccionEnvioForm()
    
    return render(request, 'ingresar_direccion_envio.html', {'form': form})

def aumentar_cantidad(request, elemento_id):
    elemento = get_object_or_404(ElementoCarrito, pk=elemento_id)
    elemento.cantidad += 1  # Aumentar la cantidad en 1
    elemento.save()
    return redirect('ver_carrito')

def disminuir_cantidad(request, elemento_id):
    elemento = get_object_or_404(ElementoCarrito, pk=elemento_id)
    if elemento.cantidad > 1:  # Verificar si la cantidad es mayor que 1 para evitar cantidades negativas
        elemento.cantidad -= 1  # Disminuir la cantidad en 1
        elemento.save()
    return redirect('ver_carrito')


def ingresar_direccion_envio(request):
    if request.method == 'POST':
        direccion = request.POST.get('direccion')
        ciudad = request.POST.get('ciudad')
        codigo_postal = request.POST.get('codigo_postal')
        # Aquí puedes hacer la validación de los datos ingresados
        DireccionEnvio.objects.create(
            direccion=direccion,
            ciudad=ciudad,
            codigo_postal=codigo_postal
        )
        # Redirigir a la página de generar orden
        return redirect('realizar_orden')
    return render(request, 'ingresar_direccion_envio.html')


#Enviar correo al hacer una orden
    
@receiver(post_save, sender=Orden)
def enviar_correo_orden(sender, instance, created, **kwargs):
    if created:
        subject = 'Nueva orden generada'
        elementos = instance.elementoorden_set.all()
        
        context = {
            'orden': instance,
            'elementos': elementos
        }
        
        template = get_template('correo_orden.html')
        content = template.render(context)
        
        email = EmailMultiAlternatives(
            subject,
            content,
            settings.EMAIL_HOST_USER,
            ['ventas@axoningenieria.cl']  # Cambiar el correo destinatario
        )
        email.attach_alternative(content, 'text/html')
        email.send()


#guarda los productos del carito en la orden       

def completar_pedido(request):
    # Obtener el carrito del usuario
    carrito_usuario = ElementoCarrito.objects.filter(usuario=request.user)
    
    # Verificar si el carrito está vacío
    if not carrito_usuario.exists():
        return redirect('carrito')

    # Crear una nueva instancia de Orden
    nueva_orden = Orden(usuario=request.user)
    nueva_orden.save()

    # Transferir los productos del carrito a la orden
    for elemento_carrito in carrito_usuario:
        nuevo_elemento_orden = ElementoOrden(
            orden=nueva_orden,
            producto=elemento_carrito.producto,
            cantidad=elemento_carrito.cantidad
        )
        nuevo_elemento_orden.save()

        # Eliminar los elementos del carrito una vez transferidos a la orden
        elemento_carrito.delete()

    # Calcular el precio total y guardarlo en la orden
    nueva_orden.precio_total = sum(item.subtotal() for item in nueva_orden.elementoorden_set.all())
    nueva_orden.save()

    # Redirigir o mostrar una página de confirmación de pedido
    return render(request, 'completar_pedido.html', {'orden': nueva_orden})


#Correo de contacto
def contacto(request):
    if request.method == "POST":
        try:
            name = request.POST['name']
            email = request.POST['email']
            subject = request.POST['subject']
            message = request.POST['message']
            
            template = render_to_string('correo_contacto.html', {
                'name': name,
                'email': email,
                'message': message
            })
            
            email_message = EmailMessage(
                subject,
                template,
                settings.EMAIL_HOST_USER,
                ['contacto@axoningenieria.cl']
            )
            
            email_message.fail_silently = False
            email_message.send()
            
            messages.success(request, 'Se ha enviado tu correo.')
        except Exception as e:
            messages.error(request, f'Error al enviar el correo: {e}')
        return render(request, 'contacto.html')
    else:
        return render(request, 'contacto.html')
    
    
#Botón de busqueda
def buscar_productos(request):
    query = request.GET.get('q')
    mensaje = None
    ultimos_productos = Producto.objects.order_by('-creado')[:4]
    resultados = Producto.objects.none()  # Inicializar con un QuerySet vacío
    
    if query:
        resultados = Producto.objects.filter(titulo__icontains=query)
        if not resultados.exists():
            mensaje = f"No se encontraron resultados para '{query}'."
    
    return render(request, 'index.html', {
        'query': query,
        'resultados': resultados,
        'mensaje': mensaje,
        'ultimos_productos': ultimos_productos
    })



def producto_detalle(request, producto_id):
    producto = Producto.objects.get(pk=producto_id)
    return render(request, 'producto.html', {'producto': producto})

#carrusel productos
def inicio(request):
    ultimos_productos = Producto.objects.order_by('-creado')[:4]
    return render(request, 'index.html', {'ultimos_productos': ultimos_productos})

def ultimos_productos(request):
    ultimos_productos = Producto.objects.order_by('-creado')[:4]
    return render(request, 'index.html', {'ultimos_productos': ultimos_productos})