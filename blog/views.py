from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Comment
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView	
from users.forms import CommentForm, PostCreateForm
from users.models import Profile
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

def home(request):
	context = {
	'posts': Post.objects.all(),
	'title': 'Blog-Home'
	}
	return render(request, 'blog/home.html', context)

class PostListView(ListView): 
	model = Post 
	template_name = 'blog/home.html' # default template naming -> <app>/<model>_<view_type>.html
	context_object_name = 'posts' 
	ordering = ['-date_posted'] #minus sign indicated ordering from latest to oldest posts
	paginate_by = 4

	def get_context_data(self, **kwargs):
		context = super(PostListView, self).get_context_data(**kwargs)
		context['title'] = 'Blog Home'
		return context

class UserPostListView(ListView):
	model = Post
	template_name = 'blog/user_posts.html'
	context_object_name = 'posts'
	paginate_by = 4

	def get_queryset(self):
		user = get_object_or_404(User, username=self.kwargs.get('username'))
		return Post.objects.filter(author=user).order_by('-date_posted')

def post_detail(request, *args, **kwargs):
	post = get_object_or_404(Post, pk=kwargs.get('pk'))
	comments = Comment.objects.filter(post=post).order_by('-id')

	if request.method == "POST":
		comment_form = CommentForm(request.POST)
		if comment_form.is_valid():
			content = request.POST.get('content')
			comment = Comment.objects.create(post=post, user=request.user, content=content)
			comment.save()
			return redirect('post-detail', post.id)
	else:
		comment_form = CommentForm()

	context = {
	"object":post,
	'comments': comments,
	"comment_form": comment_form
	}
	return render(request, 'blog/post_detail.html', context)

@login_required 
def post_create(request):
	if request.method == "POST":
		form = PostCreateForm(request.POST)
		if form.is_valid():
			title = request.POST.get('title')
			content = request.POST.get('content')
			post = Post.objects.create(title=title, content=content, author=request.user)
			post.save()

			username = request.user.username
			user = User.objects.get(username=username)
			subscribed_by_profiles = user.profile.subscribed_by.all()
			to_email = []
			from_email = settings.DEFAULT_FROM_EMAIL
			subject = 'New post by {}!'.format(username)
			for subscribed_by_profile in subscribed_by_profiles:
				to_email.append(str(subscribed_by_profile.user.email))
			contact_message = 'A new post was created just now by {} on the blog.'.format(username)
			send_mail(subject, contact_message, from_email, to_email, fail_silently=False)
			messages.success(request, 'Post made successfully!')
			return redirect('blog-home')
	else:
		form = PostCreateForm()

	context = {
		'form': form,
	}
	return render(request, 'blog/post_form.html', context)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = Post
	fields = ['title', 'content']

	def form_valid(self, form): 
		form.instance.author = self.request.user
		return super().form_valid(form)

	def test_func(self):
		post = self.get_object() #inbult method of UpdateView to get the current post we're working with
		if self.request.user == post.author: 
			return True
		else:
			return False

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Post
	success_url = '/' #for redirecting to home page after deletion

	def test_func(self):
		post = self.get_object() 
		if self.request.user == post.author: 
			return True
		else:
			return False

@login_required
def personal_feed(request):
	posts = Post.objects.all()
	profiles = request.user.profile.follows.all()

	context = {
		'posts': posts,
		'profiles': profiles,
	}
	
	return render(request, 'blog/personal_feed.html', context)

@login_required
def follow_user(request, **kwargs):
	id = request.POST.get('post_author_profile_id')
	profile = Profile.objects.get(id=id)
	profile.followed_by.add(request.user.profile)

	return redirect('blog-home')

@login_required
def unfollow_user(request, **kwargs):
	id = request.POST.get('post_author_profile_id')
	profile = Profile.objects.get(id=id)
	profile.followed_by.remove(request.user.profile)

	return redirect('blog-home')

@login_required
def subscribe_to_user(request, **kwargs):
	id = request.POST.get('post_author_profile_id')
	profile = Profile.objects.get(id=id)
	request.user.profile.subscribed_to.add(profile)

	return redirect('blog-home')

@login_required
def unsubscribe_to_user(request, **kwargs):
	id = request.POST.get('post_author_profile_id')
	profile = Profile.objects.get(id=id)
	profile.subscribed_by.remove(request.user.profile)

	return redirect('blog-home')


def about(request):
	return render(request, 'blog/about.html', {'title': 'Blog- About'})

