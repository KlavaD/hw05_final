from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User, Like
from .utils import posts_paginator


def index(request):
    post_list = Post.objects.select_related('author', 'group').all()
    page_obj = posts_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    page_obj = posts_paginator(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and author.following.filter(
        user=request.user,
    ).exists()
    post_list = author.posts.select_related('group').all()
    page_obj = posts_paginator(request, post_list)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.prefetch_related('comments__author'),
        pk=post_id
    )
    following = request.user.is_authenticated and post.author.following.filter(
        user=request.user,
    ).exists()
    form = CommentForm()
    context = {
        'author': post.author,
        'post': post,
        'form': form,
        'comments': post.comments.all(),
        'following': following,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/post_create.html', {'form': form})
    post_object: Post = form.save(commit=False)
    post_object.author = request.user
    post_object.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not post.author == request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(request, 'posts/post_create.html', {'form': form})
    form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def post_del(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not post.author == request.user:
        return redirect('posts:post_detail', post_id)
    post.delete()
    return redirect('posts:profile', request.user.username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def del_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post_id = comment.post.id
    if request.user == comment.author:
        comment.delete()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    page_obj = posts_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора username
    if request.user.username != username:
        Follow.objects.get_or_create(
            user=request.user,
            author=get_object_or_404(User, username=username)
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    get_object_or_404(Follow, author__username=username).delete()
    return redirect('posts:profile', username)


@login_required
def like_to_post(request, post_id):
    post = Post.objects.get(pk=post_id)
    post_type = ContentType.objects.get_for_model(post)
    if request.user != post.author:
        if post.likes.filter(liked_by=request.user,).exists():
            Like.objects.filter(
                content_type=post_type, object_id=post.id, liked_by=request.user
            ).delete()
        else:
            Like.objects.create(
                content_type=post_type, object_id=post.id, liked_by=request.user)

    # return redirect('posts:post_detail', post_id=post_id)
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def like_to_comment(request, comment_id):
    obj = Comment.objects.get(pk=comment_id)
    obj_type = ContentType.objects.get_for_model(obj)
    if request.user != obj.author:
        if obj.likes.filter(liked_by=request.user, ).exists():
            Like.objects.filter(
                content_type=obj_type, object_id=obj.id, liked_by=request.user
            ).delete()
        else:
            Like.objects.create(
                content_type=obj_type, object_id=obj.id, liked_by=request.user)
    return redirect('posts:post_detail', post_id=obj.post_id)
