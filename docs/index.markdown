---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: home
---

<h1>{{ site.posts.first.title }}</h1>
{{ site.posts.first.content }}

<h1>Posts anteriores</h1>
<ul>
{% for post in site.posts offset:1 %}
  <li>
    <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
  </li>
{% endfor %}
</ul>
