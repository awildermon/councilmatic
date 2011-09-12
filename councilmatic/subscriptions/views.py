from django.views import generic as views
from django import http
from haystack import views as haystack_views
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response

import subscriptions.forms as forms
import subscriptions.models as models

class SingleSubscriptionMixin (object):
    feed_data = None
    """A factory for the feed_data object that describes this content feed"""

    def get_content_feed(self, *args, **kwargs):
        feed_data = self.feed_data(*args, **kwargs)
        return models.ContentFeed.factory(feed_data)

    def get_subscription(self, feed):
        if self.request.user and self.request.user.is_authenticated():
            try:
                subscriber = self.request.user.subscriber

            # If the user doesn't have a subscriber attribute, then they must
            # not be subscribed.
            except models.Subscriber.DoesNotExist:
                return None

            return subscriber.subscription(feed)

        return None

    def get_subscription_form(self, feed):
        if self.request.user and self.request.user.is_authenticated():
            try:
                subscriber = self.request.user.subscriber

            except models.Subsciber.DoesNotExist:
                return None

            if not self.request.user.subscriber.is_subscribed(feed):
                form = forms.SubscriptionForm({'feed': feed,
                                               'subscriber': subscriber})
                return form

        return None

    def get_context_data(self, **kwargs):
        context_data = super(SingleSubscriptionMixin, self).get_context_data(**kwargs)

        feed = self.get_content_feed()
        subscription = self.get_subscription(feed)
        subscription_form = self.get_subscription_form(feed)
        is_subscribed = (subscription is not None)

        context_data.update({'feed': feed,
                             'subscription': subscription,
                             'subscription_form': subscription_form,
                             'is_subscribed': is_subscribed})
        return context_data


class CreateSubscriptionView (views.CreateView):
    model = models.Subscription


class DeleteSubscriptionView (views.DeleteView):
    model = models.Subscription


class SearchView (haystack_views.SearchView):
    def __init__(self, *args, **kwds):
        super(SearchView, self).__init__(form_class=forms.SimpleSearchForm, *args, **kwds)

    def get_embedded_subscribe_form(self):
        return forms.SearchSubscriptionForm()

    def extra_context(self):
        return { 'subs_form': self.get_embedded_subscribe_form() }

    def create_response(self):
        """
        Generates the actual HttpResponse to send back to the user.
        """
        (paginator, page) = self.build_page()

        context = {
            'query': self.query,
            'form': self.form,
            'page': page,
            'object_list': [result.object for result in page.object_list],
            'paginator': paginator,
            'suggestion': None,
        }

        context.update(self.extra_context())
        return render_to_response(self.template, context, context_instance=self.context_class(self.request))


class SubscribeToSearchView (views.CreateView):
    model = models.SearchSubscription
    template_name = "subscriptions/searchsubscription_edit.html"


def subscribe(request):
    subscriber = request.user.subscriber
    feed = ContentFeed.object.get(request.REQUEST['feed'])
    redirect_to = request.REQUEST['next']

    subscriber.subscribe(feed)
    return HttpResponseRedirect(redirect_to)


#    def get_subscription_form(self):
#        pass
#
#    def __call__(self, request):
#        if request.method == 'POST':
#
#            subs_form = self.get_subscription_form()
#        else:
#            return super(SubscribeToSearchView, self).__call__(request)
