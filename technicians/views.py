from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Technician, TechnicianAssistant, TechnicianService, TechnicianRecommendation
from .forms import TechnicianForm, TechnicianAssistantForm, TechnicianServiceForm, TechnicianRecommendationForm
from users.decorators import role_required


@login_required
def technician_list(request):
    """List all technicians"""
    technicians = Technician.objects.filter(is_active=True).prefetch_related('assistants', 'services')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        technicians = technicians.filter(
            Q(company_name__icontains=search_query) |
            Q(technician_name__icontains=search_query) |
            Q(specialization__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    return render(request, 'technicians/list.html', {
        'technicians': technicians,
        'search_query': search_query,
    })


@login_required
def technician_detail(request, pk):
    """View technician details with assistants and services"""
    technician = get_object_or_404(Technician, pk=pk)
    assistants = technician.assistants.filter(is_active=True)
    services = technician.services.filter(is_active=True)
    recommendations = technician.recommendations.order_by('-created_at')[:10]
    
    return render(request, 'technicians/detail.html', {
        'technician': technician,
        'assistants': assistants,
        'services': services,
        'recommendations': recommendations,
    })


@login_required
@role_required(['super_admin', 'admin'])
def technician_create(request):
    """Create new technician"""
    if request.method == 'POST':
        form = TechnicianForm(request.POST)
        if form.is_valid():
            technician = form.save()
            messages.success(request, f'Technician {technician.technician_name} from {technician.company_name} created successfully!')
            return redirect('technicians:detail', pk=technician.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = TechnicianForm()
    
    return render(request, 'technicians/form.html', {'form': form, 'title': 'Add Technician'})


@login_required
@role_required(['super_admin', 'admin'])
def technician_update(request, pk):
    """Update technician"""
    technician = get_object_or_404(Technician, pk=pk)
    
    if request.method == 'POST':
        form = TechnicianForm(request.POST, instance=technician)
        if form.is_valid():
            form.save()
            messages.success(request, 'Technician updated successfully!')
            return redirect('technicians:detail', pk=technician.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = TechnicianForm(instance=technician)
    
    return render(request, 'technicians/form.html', {'form': form, 'title': 'Edit Technician', 'technician': technician})


@login_required
@role_required(['super_admin', 'admin'])
def assistant_create(request, technician_pk):
    """Add assistant to technician"""
    technician = get_object_or_404(Technician, pk=technician_pk)
    
    if request.method == 'POST':
        form = TechnicianAssistantForm(request.POST)
        if form.is_valid():
            assistant = form.save(commit=False)
            assistant.technician = technician
            assistant.save()
            messages.success(request, f'Assistant {assistant.name} added successfully!')
            return redirect('technicians:detail', pk=technician.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = TechnicianAssistantForm()
    
    return render(request, 'technicians/assistant_form.html', {
        'form': form, 
        'technician': technician,
        'title': f'Add Assistant for {technician.technician_name}'
    })


@login_required
@role_required(['super_admin', 'admin'])
def service_create(request, technician_pk):
    """Add service to technician"""
    technician = get_object_or_404(Technician, pk=technician_pk)
    
    if request.method == 'POST':
        form = TechnicianServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.technician = technician
            service.save()
            messages.success(request, f'Service {service.service_name} added successfully!')
            return redirect('technicians:detail', pk=technician.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = TechnicianServiceForm()
    
    return render(request, 'technicians/service_form.html', {
        'form': form, 
        'technician': technician,
        'title': f'Add Service for {technician.technician_name}'
    })


@login_required
@role_required(['super_admin', 'admin'])
def recommendation_create(request):
    """Create technician recommendation for an asset"""
    if request.method == 'POST':
        form = TechnicianRecommendationForm(request.POST)
        if form.is_valid():
            recommendation = form.save()
            messages.success(request, 'Recommendation added successfully!')
            return redirect('technicians:detail', pk=recommendation.technician.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = TechnicianRecommendationForm()
        # Pre-select technician or asset if passed in URL
        initial = {}
        technician_id = request.GET.get('technician')
        asset_id = request.GET.get('asset')
        if technician_id:
            initial['technician'] = technician_id
        if initial:
            form = TechnicianRecommendationForm(initial=initial)
    
    return render(request, 'technicians/recommendation_form.html', {
        'form': form,
        'title': 'Add Technician Recommendation'
    })


@login_required
def recommendation_list(request):
    """List all technician recommendations"""
    recommendations = TechnicianRecommendation.objects.select_related('technician').order_by('-created_at')
    
    # Filter by completion status
    status_filter = request.GET.get('status')
    if status_filter == 'pending':
        recommendations = recommendations.filter(is_completed=False)
    elif status_filter == 'completed':
        recommendations = recommendations.filter(is_completed=True)
    
    return render(request, 'technicians/recommendation_list.html', {
        'recommendations': recommendations,
        'status_filter': status_filter,
    })
