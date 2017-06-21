from django.shortcuts import render


def handle_500(request):
    return render(request, '500.html', status=500)


def handle_404(request):
    return render(request, '400.html', status=404)
