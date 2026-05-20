| Command | Description |
| -------- | -----------|
| `docker compose -f docker/long_running/minio/docker-compose.yaml down -v` | Docker compose while passing a filepath |
| `docker build -f ./docker/ephemeral/Dockerfile__ephemeral_etl -t ephemeral_etl .` | Build a docker image based on a Dockerfile, container name, and build context |
| `docker image ls` | List docker images |
| `docker system df -v` | Show system wide disk usage |
| `docker image prune` | Prune unused images |
| `docker container prune` | Remove stopped containers |
| `docker volume prune` | Remove usused volumes |
| `docker network prune` | Remove unused networks |
| `docker system prune -a --volumes` | Aggressive cleanup |
| `docker system prune -af && docker builder prune -af` | Common CI cleanup |

