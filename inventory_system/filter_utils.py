"""
Utility functions for persisting filter parameters in session.
This allows users to return to a page with their previous filters still applied.
"""

import copy


def get_session_key(view_name):
    """Generate a session key for a given view name."""
    return f'filters_{view_name}'


def save_filters_to_session(request, view_name, filter_params):
    """
    Save filter parameters to session for a specific view.
    
    Args:
        request: The current request object
        view_name: A unique identifier for the view (e.g., 'asset_list')
        filter_params: Dict of filter parameters to save
    """
    session_key = get_session_key(view_name)
    
    # Create a copy to avoid modifying the original
    filters_to_save = copy.deepcopy(filter_params)
    
    # Remove 'page' from saved filters (we don't want to restore page number)
    filters_to_save.pop('page', None)
    
    request.session[session_key] = filters_to_save
    request.session.modified = True


def restore_filters_from_session(request, view_name, allowed_params=None):
    """
    Restore filter parameters from session for a specific view.
    
    Args:
        request: The current request object
        view_name: A unique identifier for the view
        allowed_params: List of allowed parameter names (if None, all are allowed)
    
    Returns:
        Dict of restored filter parameters
    """
    session_key = get_session_key(view_name)
    saved_filters = request.session.get(session_key, {})
    
    if allowed_params:
        # Only return allowed parameters
        return {k: v for k, v in saved_filters.items() if k in allowed_params}
    
    return saved_filters


def clear_filters_from_session(request, view_name):
    """
    Clear saved filter parameters from session for a specific view.
    
    Args:
        request: The current request object
        view_name: A unique identifier for the view
    """
    session_key = get_session_key(view_name)
    if session_key in request.session:
        del request.session[session_key]
        request.session.modified = True


def merge_filters_with_session(request, view_name, current_filters, allowed_params=None):
    """
    Merge current filter parameters with saved session filters.
    Current filters take precedence over saved filters.
    
    This should be called at the beginning of a list view to get the
    combined filters (URL params + session saved params).
    
    Args:
        request: The current request object
        view_name: A unique identifier for the view
        current_filters: Dict of current filter parameters from request.GET
        allowed_params: List of allowed parameter names
    
    Returns:
        Dict of merged filter parameters
    """
    # Get saved filters from session
    saved_filters = restore_filters_from_session(request, view_name, allowed_params)
    
    # Start with saved filters
    merged = copy.deepcopy(saved_filters)
    
    # Override with current filters (non-empty values)
    for key, value in current_filters.items():
        if value and value.strip():
            merged[key] = value
        elif key in current_filters and not value:
            # Explicitly empty value in URL means clear this filter
            merged.pop(key, None)
    
    # If user submitted the filter form (indicated by any filter param being present),
    # save the new filters to session
    if current_filters:
        # Only save if there's an actual filter form submission (not just page navigation)
        non_page_params = {k: v for k, v in current_filters.items() if k != 'page'}
        if non_page_params:
            save_filters_to_session(request, view_name, merged)
    
    return merged


def handle_filter_request(request, view_name, param_names):
    """
    Main handler for filter persistence.
    
    Use this in your view to get the effective filters that should be applied.
    
    Args:
        request: The current request object
        view_name: A unique identifier for the view
        param_names: List of filter parameter names to handle
    
    Returns:
        Tuple of (filters_dict, should_clear_session)
        - filters_dict: The effective filters to apply
        - should_clear_session: Boolean indicating if we should clear the session
    """
    # Check if this is a "clear filters" request
    if request.GET.get('clear_filters'):
        clear_filters_from_session(request, view_name)
        return {}, True
    
    # Get current filters from request
    current_filters = {}
    for param in param_names:
        value = request.GET.get(param, '')
        if value:
            current_filters[param] = value
    
    # Check if any explicit filters were passed in URL
    has_explicit_filters = bool(current_filters)
    
    # Merge with session filters
    effective_filters = merge_filters_with_session(
        request, view_name, current_filters, param_names
    )
    
    # If user is submitting new filters, save them
    if has_explicit_filters:
        save_filters_to_session(request, view_name, effective_filters)
    
    return effective_filters, False
