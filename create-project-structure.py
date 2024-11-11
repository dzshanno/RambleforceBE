import os

# Create the app directory and its subdirectories
os.makedirs("app/database")
os.makedirs("app/routers")
os.makedirs("app/schemas")
os.makedirs("app/utils")

# Create the tests directory
os.makedirs("tests")

# Create the migrations directory
os.makedirs("migrations")

# Create empty __init__.py files
open("app/__init__.py", "w").close()
open("app/database/__init__.py", "w").close()
open("app/routers/__init__.py", "w").close()
open("app/schemas/__init__.py", "w").close()
open("app/utils/__init__.py", "w").close()
open("tests/__init__.py", "w").close()

# Create files with comments
with open("app/main.py", "w") as file:
    file.write("# The main FastAPI application file")

with open("app/database/session.py", "w") as file:
    file.write("# Contains the database session configuration")

with open("app/database/models.py", "w") as file:
    file.write("# Defines the SQLAlchemy models")

with open("app/routers/attendees.py", "w") as file:
    file.write("# Contains route handlers for attendee-related endpoints")

with open("app/routers/merchandise.py", "w") as file:
    file.write("# Contains route handlers for merchandise-related endpoints")

with open("app/routers/events.py", "w") as file:
    file.write("# Contains route handlers for event-related endpoints")

with open("app/routers/comments.py", "w") as file:
    file.write("# Contains route handlers for comment-related endpoints")

with open("app/schemas/attendee.py", "w") as file:
    file.write("# Defines the Pydantic model for attendees")

with open("app/schemas/merchandise.py", "w") as file:
    file.write("# Defines the Pydantic model for merchandise")

with open("app/schemas/event.py", "w") as file:
    file.write("# Defines the Pydantic model for events")

with open("app/schemas/comment.py", "w") as file:
    file.write("# Defines the Pydantic model for comments")

with open("tests/test_attendees.py", "w") as file:
    file.write("# Contains tests for attendee-related functionality")

with open("tests/test_merchandise.py", "w") as file:
    file.write("# Contains tests for merchandise-related functionality")

with open("tests/test_events.py", "w") as file:
    file.write("# Contains tests for event-related functionality")

with open("tests/test_comments.py", "w") as file:
    file.write("# Contains tests for comment-related functionality")

with open("requirements.txt", "w") as file:
    file.write("# File specifying the project dependencies")

with open(".env", "w") as file:
    file.write("# File for storing environment variables (e.g., database credentials)")

with open(".gitignore", "w") as file:
    file.write("# File specifying files and directories to be ignored by Git")

with open("README.md", "w") as file:
    file.write("# File providing an overview and instructions for the project")

with open("Dockerfile", "w") as file:
    file.write("# File for containerizing the application using Docker")
