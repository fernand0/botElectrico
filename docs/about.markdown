---
layout: page
title: Acerca de / About
permalink: /about/
---

Esta página se actualiza cada noche (alrededor de las 21:00) y muestra la evolución de los precios según la tarifa PVPC para el día siguiente. Se muestra en formato gráfico y también una tabla con los valores publicados en la página web del [API  e·sios](https://api.esios.ree.es/) de [Red Eléctrica Española](https://www.ree.es/es).

Se puede seguir esta información en esta página (una vez al día) y en las siguientes redes sociales (cada hora):

{% include svg-icons.html %}

El código que genera estas páginas está disponible en. Se basa en <a href="https://jekyllrb.com">Jekyll</a> con algunas modificaciones del tema <a href="https://github.com/jekyll/minima">Minima</a> y un programa escrito en Python:

<ul>
{% if site.footer-links.github %} <li> <svg class="svg-icon grey"> <use xlink:href="{{ 'assets/minima-social-icons.svg#github' | relative_url }}"></use> </svg> GitHub: <a target="_blank" href="https://github.com/{{ site.footer-links.github }}" class="u-url url" rel="me">https://github.com/{{ site.footer-links.github }}</a></li>{% endif %} 
{% if site.footer-links.url %} <li> <svg class="svg-icon grey"> <use xlink:href="{{ 'assets/minima-social-icons.svg#url' | relative_url }}"></use> </svg> Datos (formato *json*): <a target="_blank" href="{{ site.footer-links.url }}" class="u-url url" >{{ site.footer-links.url }}</a></li>{% endif %} 
</ul>

Se puede contactar con el autor a través de:

<ul>
{% if site.footer-links.email %} <li> <svg class="svg-icon grey"> <use xlink:href="{{ 'assets/minima-social-icons.svg#email' | relative_url }}"></use> </svg> eMail: <a target="_blank" href="mailto:{{ site.footer-links.github }}" class="u-url url" rel="me">{{ site.footer-links.email }}</a></li>{% endif %} 
</ul>


