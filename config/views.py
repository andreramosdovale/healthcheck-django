from django.shortcuts import redirect, render


def home_view(request):
    if request.user.is_authenticated:
        return redirect("measurements:list")
    return render(request, "home.html")
