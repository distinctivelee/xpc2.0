from django.shortcuts import render
from django.core.paginator import Paginator
from web.models.post import Post


def show_list(request):
    post_list = Post.objects.order_by("-like_counts")
    paginator = Paginator(post_list,40)
    posts = paginator.page(1)
    return render(request,'post_list.html', {'posts':posts})