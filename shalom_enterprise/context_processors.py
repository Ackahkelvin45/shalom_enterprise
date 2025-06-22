from settings.models import Settings,SocialMedia
def global_data(request):
    settings = Settings.objects.first() # Example: get 5 items
    social_media = SocialMedia.objects.first()  # Example: get 5 items


    return {
        'global_settings': settings,  # Single object instead of queryset
        'global_social_media': social_media,  # Queryset or single object
    }