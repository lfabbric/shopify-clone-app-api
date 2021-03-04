# shopify-clone-app-api


# Testing
docker-compose run app sh -c "python manage.py test && flake8"

# VSCode
1) Install the Remote development Extension Pack in VSCode
2) Ensure you are in the main app folder (parralel to the docker)
2) Boot Up Docker Environment
  a) ctrl+shift+P
  b) select Remote-Containers: Open folder in Container
  c) click open (as it is in the root)
  d) select the docker + compose package
