from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from .models import Post, Tag
from django.db.models import Q, Count
from django.contrib import messages
from .forms import ShareForm, ContactForm, CommentForm
from django.urls import reverse
from django.http import HttpResponse
from django.core.mail import send_mail
# Create your views here.


class BlogHome(generic.ListView):

    model = Post

    paginate_by = 4

    template_name = 'post/home.html'


class PostDetailView(generic.DetailView):

    model = Post

    def get_context_data(self, *args, **kwargs):

        ctx = super().get_context_data(*args, **kwargs)

        ctx['form'] = CommentForm

        similar_post_tag = self.object.tags.values_list("id", flat=True)

        similar_posts = Post.objects.filter(
            tags__in=similar_post_tag).exclude(id=self.object.id)

        similar_posts = similar_posts.annotate(
            same_tags=Count('tags')).order_by('same_tags', '-publish')[:4]

        ctx['similar_posts'] = similar_posts

        return ctx

class SearchSimilarTag(generic.ListView):

    template_name = 'post/home.html'

    model = Post

    def get_queryset(self, *args, **kwargs):

        data = self.request.GET.get('q', None)

        if data:

            tag = get_object_or_404(Tag, name=data)

            objs = tag.post_set.all()

            return objs

        return super().get_queryset()

class SearchView(generic.View):

    def get(self, request):

        ctx = {
        }

        data = request.GET.get('q', None)

        if data:
            queryset = Post.objects.filter(
                Q(title__icontains=data) |
                Q(content__icontains=data) |
                Q(author__username__icontains=data)
            )

            ctx = {
                "object_list": queryset
            }

            messages.info(request, f"Search result for {data}")

            return render(request, 'post/home.html', ctx)

        ctx['object_list'] = Post.objects.all()

        return render(request, 'post/home.html', ctx)


def share_post_view(request, pk):

    form = ShareForm(request.POST or None)

    instance = None

    if pk:

        # instance = Post.objects.get(pk=pk)

        instance = get_object_or_404(Post, pk=pk)

    context = {
        'form': form,
        'instance': instance
    }

    if request.method == "POST":

        if form.is_valid():

            cd = form.cleaned_data

            name = cd.get('name')

            to_email = cd.get('to')

            from_email = cd.get('email')

            message = cd.get('message')

            link = reverse('post:detail', kwargs={"slug": instance.slug})

            subject = f"{name} ({from_email}) recommend you reading {instance.title}"

            body = f"Read {instance.title} at {link}\n\n{message}"

            send_mail(subject, body, 'myblog@myblog.com', [to_email])

            context['email_sent'] = True

    return render(request, 'post/share_post.html', context)


class ContactView(generic.TemplateView):

    template_name = "post/contact.html"

    def get_context_data(self):

        form = ContactForm

        ctx = {
            "form": form
        }

        return ctx

    def post(self, request):

        form = ContactForm(request.POST or None)

        context = {
            'form': form,
        }

        if form.is_valid():

            cd = form.cleaned_data

            name = cd.get('name')

            from_email = cd.get('email')

            message = cd.get('message')

            subject = "Contact from user"

            send_mail(subject, message, from_email, ['myblog@myblog.com', ])

            context['email_sent'] = True

        return render(request, 'post/contact.html', context)


def post_comment(request, slug):

    if request.method == "POST":

        form = CommentForm(request.POST or None)

        post = get_object_or_404(Post, slug=slug)

        ctx = {
            "slug": slug,
            "object": post,
            'form': form,
        }
        if form.is_valid():

            comment = form.save(commit=False)

            comment.post = post

            comment.save()

            ctx['new_comment'] = comment

            return render(request, 'post/post_detail.html', ctx)

    return redirect(reverse('post:detail', kwargs={"slug": slug}))

