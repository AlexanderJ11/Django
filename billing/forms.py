from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Brand
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
