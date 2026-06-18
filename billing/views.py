from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.http import JsonResponse
from .models import *
from .forms import SignUpForm, BrandForm, InvoiceForm, InvoiceDetailFormSet
from shared.mixins import StaffRequiredMixin, ExportMixin
from shared.decorators import audit_action
from decimal import Decimal


# === HOME (Página principal) ===
@login_required
def home(request):
    """Vista principal del sistema. Muestra resumen general."""
    context = {
        'total_brands': Brand.objects.count(),
        'total_products': Product.objects.count(),
        'total_customers': Customer.objects.count(),
        'total_invoices': Invoice.objects.count(),
        'recent_invoices': Invoice.objects.all()[:5],
        'low_stock': Product.objects.filter(stock__lte=5, is_active=True),
    }
    return render(request, 'billing/home.html', context)


# === REGISTRO ===
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('billing:brand_list')
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


# === BRAND (FBV) ===
@login_required
@audit_action('LIST_BRANDS')
def brand_list(request):
    brands = Brand.objects.all()
    return render(request, 'billing/brand_list.html', {'brands': brands})

@login_required
@audit_action('CREATE_BRAND')
def brand_create(request):
    if request.method == 'POST':
        form = BrandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Brand created!')
            return redirect('billing:brand_list')
    else: form = BrandForm()
    return render(request, 'billing/brand_form.html', {'form': form, 'title': 'Create Brand'})

@login_required
@audit_action('UPDATE_BRAND')
def brand_update(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        form = BrandForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, 'Brand updated!')
            return redirect('billing:brand_list')
    else: form = BrandForm(instance=brand)
    return render(request, 'billing/brand_form.html', {'form': form, 'title': 'Edit Brand'})

@login_required
@audit_action('DELETE_BRAND')
def brand_delete(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        brand.delete()
        messages.success(request, 'Brand deleted!')
        return redirect('billing:brand_list')
    return render(request, 'billing/brand_confirm_delete.html', {'object': brand})


# === PRODUCTGROUP (CBV) ===
class ProductGroupListView(LoginRequiredMixin, ListView):
    model = ProductGroup; template_name = 'billing/productgroup_list.html'; context_object_name = 'items'

class ProductGroupCreateView(LoginRequiredMixin, CreateView):
    model = ProductGroup; fields = ['name', 'is_active']; template_name = 'billing/productgroup_form.html'; success_url = reverse_lazy('billing:productgroup_list')

class ProductGroupUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductGroup; fields = ['name', 'is_active']; template_name = 'billing/productgroup_form.html'; success_url = reverse_lazy('billing:productgroup_list')

class ProductGroupDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = ProductGroup; template_name = 'billing/productgroup_confirm_delete.html'; success_url = reverse_lazy('billing:productgroup_list')


# === SUPPLIER (CBV) ===
class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier; template_name = 'billing/supplier_list.html'; context_object_name = 'items'

class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier; fields = ['name', 'contact_name', 'email', 'phone', 'address', 'is_active']; template_name = 'billing/supplier_form.html'; success_url = reverse_lazy('billing:supplier_list')

class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier; fields = ['name', 'contact_name', 'email', 'phone', 'address', 'is_active']; template_name = 'billing/supplier_form.html'; success_url = reverse_lazy('billing:supplier_list')

class SupplierDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Supplier; template_name = 'billing/supplier_confirm_delete.html'; success_url = reverse_lazy('billing:supplier_list')


# === PRODUCT (CBV) ===
class ProductListView(LoginRequiredMixin, ExportMixin, ListView):
    model = Product
    template_name = 'billing/product_list.html'
    context_object_name = 'items'
    paginate_by = 10
    export_filename = 'products'
    export_title    = 'Product List'
    export_fields   = [
        ('Name',      'name'),
        ('Brand',     'brand__name'),
        ('Group',     'group__name'),
        ('Price',     'unit_price'),
        ('Stock',     'stock'),
        ('Status',    lambda obj: 'Active' if obj.is_active else 'Inactive'),
        ('Suppliers', lambda obj: ', '.join(s.name for s in obj.suppliers.all())),
    ]

    def get_queryset(self):
        qs = Product.objects.select_related('brand', 'group').prefetch_related('suppliers')
        g = self.request.GET
        if name := g.get('name', '').strip():
            qs = qs.filter(name__icontains=name)
        if brand := g.get('brand', ''):
            qs = qs.filter(brand_id=brand)
        if group := g.get('group', ''):
            qs = qs.filter(group_id=group)
        if supplier := g.get('supplier', ''):
            qs = qs.filter(suppliers__id=supplier)
        if price_min := g.get('price_min', '').strip():
            qs = qs.filter(unit_price__gte=price_min)
        if price_max := g.get('price_max', '').strip():
            qs = qs.filter(unit_price__lte=price_max)
        if stock_min := g.get('stock_min', '').strip():
            qs = qs.filter(stock__gte=stock_min)
        if stock_max := g.get('stock_max', '').strip():
            qs = qs.filter(stock__lte=stock_max)
        if (is_active := g.get('is_active', '')) in ('true', 'false'):
            qs = qs.filter(is_active=(is_active == 'true'))
        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['brands'] = Brand.objects.order_by('name')
        ctx['groups'] = ProductGroup.objects.order_by('name')
        ctx['suppliers_list'] = Supplier.objects.order_by('name')
        # q sin 'page' para armar URLs de paginación con filtros preservados
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['q'] = params
        return ctx

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product; fields = ['name', 'description', 'brand', 'group', 'suppliers', 'unit_price', 'stock', 'is_active']; template_name = 'billing/product_form.html'; success_url = reverse_lazy('billing:product_list')

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product; fields = ['name', 'description', 'brand', 'group', 'suppliers', 'unit_price', 'stock', 'is_active']; template_name = 'billing/product_form.html'; success_url = reverse_lazy('billing:product_list')

class ProductDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Product; template_name = 'billing/product_confirm_delete.html'; success_url = reverse_lazy('billing:product_list')


# === CUSTOMER (CBV) ===
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer; template_name = 'billing/customer_list.html'; context_object_name = 'items'

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer; fields = ['dni', 'first_name', 'last_name', 'email', 'phone', 'address', 'is_active']; template_name = 'billing/customer_form.html'; success_url = reverse_lazy('billing:customer_list')

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer; fields = ['dni', 'first_name', 'last_name', 'email', 'phone', 'address', 'is_active']; template_name = 'billing/customer_form.html'; success_url = reverse_lazy('billing:customer_list')

class CustomerDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Customer; template_name = 'billing/customer_confirm_delete.html'; success_url = reverse_lazy('billing:customer_list')


# =============================================
# CRUD DE INVOICE - VISTAS BASADAS EN FUNCIONES
# =============================================

@login_required
def invoice_list(request):
    """Lista todas las facturas con sus totales."""
    invoices = Invoice.objects.select_related('customer').all()
    return render(request, 'billing/invoice_list.html', {'items': invoices})

@login_required
def product_api(request, pk):
    """Devuelve precio y stock de un producto en JSON para el formulario de factura."""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return JsonResponse({'price': str(product.unit_price), 'stock': product.stock})

@login_required
def invoice_create(request):
    """Crea factura con sus líneas de detalle."""
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceDetailFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            # Validar stock antes de guardar
            stock_errors = []
            for detail_form in formset:
                cd = detail_form.cleaned_data
                if not cd or cd.get('DELETE'):
                    continue
                product = cd.get('product')
                quantity = cd.get('quantity') or 0
                if product and quantity > 0:
                    if quantity > product.stock:
                        stock_errors.append(
                            f'Stock insuficiente para "{product.name}": '
                            f'solicitado {quantity}, disponible {product.stock}.'
                        )

            if stock_errors:
                for msg in stock_errors:
                    messages.error(request, msg)
            else:
                invoice = form.save(commit=False)
                invoice.save()
                formset.instance = invoice
                formset.save()

                # Reducir stock de cada producto
                for detail in invoice.details.all():
                    detail.product.stock -= detail.quantity
                    detail.product.save(update_fields=['stock'])

                subtotal = sum(d.subtotal for d in invoice.details.all())
                invoice.subtotal = subtotal
                invoice.tax = subtotal * Decimal('0.15')
                invoice.total = invoice.subtotal + invoice.tax
                invoice.save()
                messages.success(request, f'Factura #{invoice.id} creada. Total: ${invoice.total}')
                return redirect('billing:invoice_list')
    else:
        form = InvoiceForm()
        formset = InvoiceDetailFormSet()
    return render(request, 'billing/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Invoice',
    })

@login_required
def invoice_detail(request, pk):
    """Muestra el detalle completo de una factura."""
    invoice = get_object_or_404(
        Invoice.objects.select_related('customer').prefetch_related('details__product'),
        pk=pk
    )
    return render(request, 'billing/invoice_detail.html', {'invoice': invoice})

@login_required
def invoice_delete(request, pk):
    """Elimina una factura y todos sus detalles (CASCADE)."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice_id = invoice.id
        invoice.delete()
        messages.success(request, f'Invoice #{invoice_id} deleted!')
        return redirect('billing:invoice_list')
    return render(request, 'billing/invoice_confirm_delete.html', {'object': invoice})