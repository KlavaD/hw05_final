from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm, ChangeForm
from .models import User


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


@login_required
def change_user_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user == request.user:
        return redirect('posts:profile', user_id)
    form = ChangeForm(
        request.POST or None,
        files=request.FILES or None,
        instance=user
    )
    if not form.is_valid():
        return render(request, 'users/signup.html', {'form': form})
    form.save()
    return redirect('posts:profile', user.username)
