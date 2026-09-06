FROM nginx:alpine
COPY superstore-dashboard.html /usr/share/nginx/html/index.html
COPY superstore_presentation.html /usr/share/nginx/html/presentation.html
COPY media/ /usr/share/nginx/html/media/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
