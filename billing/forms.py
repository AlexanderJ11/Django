from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Brand, Product
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceDetail

class InvoiceForm(forms.ModelForm):
    """Formulario para cabecera de factura."""
    class Meta:
        model = Invoice
        fields = ['customer']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
        }

class InvoiceDetailForm(forms.ModelForm):
    """Formulario para línea de detalle. El precio se bloquea al valor del producto."""
    class Meta:
        model = InvoiceDetail
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select detail-product'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control detail-quantity', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control detail-price',
                'step': '0.01',
                'readonly': 'readonly',
                'tabindex': '-1',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        # Siempre forzar el precio del producto, ignorando lo que venga del POST
        if product:
            cleaned_data['unit_price'] = product.unit_price
        return cleaned_data

InvoiceDetailFormSet = inlineformset_factory(
    Invoice,
    InvoiceDetail,
    form=InvoiceDetailForm,
    extra=3,
    can_delete=True,
)

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class':'form-control'}))
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class':'form-control'}))
    class Meta:
        model = User
        fields = ['username','first_name','last_name','email','password1','password2']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields: self.fields[f].widget.attrs['class'] = 'form-control'

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control','rows':3}),
            'is_active': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }


class ProductForm(forms.ModelForm):
    """Formulario centralizado para creación y edición de productos."""

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'image',
            'brand', 'group', 'suppliers',
            'unit_price', 'stock', 'is_active',
        ]
        labels = {
            'name':        'Nombre del producto',
            'description': 'Descripción',
            'image':       'Imagen del producto',
            'brand':       'Marca',
            'group':       'Grupo / Categoría',
            'suppliers':   'Proveedores',
            'unit_price':  'Precio unitario ($)',
            'stock':       'Stock disponible',
            'is_active':   'Producto activo',
        }
        help_texts = {
            'name':        'Nombre completo del producto.',
            'description': 'Descripción opcional.',
            'image':       'Formatos aceptados: JPG, PNG, WEBP.',
            'suppliers':   'Mantén Ctrl (o Cmd) para seleccionar varios.',
            'unit_price':  'Debe ser mayor que 0.',
            'stock':       'Cantidad disponible en inventario.',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Laptop HP ProBook 450 G9',
                'autofocus': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción opcional del producto…',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_image',
            }),
            'brand':     forms.Select(attrs={'class': 'form-select'}),
            'group':     forms.Select(attrs={'class': 'form-select'}),
            'suppliers': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'id_unit_price',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': '0',
                'id': 'id_stock',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
            }),
        }
        error_messages = {
            'name':       {'required': 'El nombre del producto es obligatorio.'},
            'brand':      {'required': 'Seleccione una marca.'},
            'group':      {'required': 'Seleccione un grupo/categoría.'},
            'unit_price': {
                'required': 'Ingrese el precio unitario.',
                'invalid':  'Ingrese un valor numérico válido.',
            },
            'stock': {'required': 'Ingrese el stock disponible.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mark fields with errors using Bootstrap's is-invalid class
        for field_name in self.errors:
            if field_name in self.fields:
                widget = self.fields[field_name].widget
                cls = widget.attrs.get('class', '')
                if 'is-invalid' not in cls:
                    widget.attrs['class'] = cls + ' is-invalid'

    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if price is not None and price <= 0:
            raise forms.ValidationError('El precio unitario debe ser mayor que cero.')
        return price
