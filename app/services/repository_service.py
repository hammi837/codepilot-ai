from app.repositories.repository_repository import RepositoryRepository
from app.schemas.repository import RepositoryCreateRequest, RepositoryResponse
from app.schemas.indexing import FileMetadataResponse
import os
from pathlib import Path
from git import Repo
from typing import List


class RepositoryService:
    def __init__(self, repository_repository: RepositoryRepository) -> None:
        self.repository_repository = repository_repository

    def list_repositories(self, user_id: int) -> list[RepositoryResponse]:
        repos = self.repository_repository.list_for_user(user_id)
        return [
            RepositoryResponse(
                id=repo.id,
                github_repo_id=repo.github_repo_id,
                repo_name=repo.repo_name,
                branch=repo.branch,
                language=repo.language,
                private=repo.private,
                clone_url=repo.clone_url,
            )
            for repo in repos
        ]

    def connect_repository(self, user_id: int, payload: RepositoryCreateRequest) -> RepositoryResponse:
        repo = self.repository_repository.create(
            user_id=user_id,
            github_repo_id=payload.github_repo_id,
            repo_name=payload.repo_name,
            branch=payload.branch,
            language=payload.language,
            private=payload.private,
            clone_url=payload.clone_url,
        )
        return RepositoryResponse(
            id=repo.id,
            github_repo_id=repo.github_repo_id,
            repo_name=repo.repo_name,
            branch=repo.branch,
            language=repo.language,
            private=repo.private,
            clone_url=repo.clone_url,
        )

    def clone_repository(self, repository: str) -> str:
        workspace_dir = Path("workspace")
        workspace_dir.mkdir(exist_ok=True)
        repo_name = repository.split("/")[-1]
        repo_path = workspace_dir / repo_name
        
        if repo_path.exists() and (repo_path / ".git").exists():
            return str(repo_path)
            
        repo_url = f"https://github.com/{repository}.git"
        # Optional: Add github token for private repos here
        
        Repo.clone_from(repo_url, repo_path)
        return str(repo_path)

    def _get_language(self, ext: str) -> str:
        ext_map = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".tsx": "TypeScript React", ".jsx": "JavaScript React",
            ".html": "HTML", ".css": "CSS", ".md": "Markdown",
            ".json": "JSON", ".go": "Go", ".java": "Java",
            ".cpp": "C++", ".c": "C", ".rs": "Rust", ".sh": "Shell",
            ".yml": "YAML", ".yaml": "YAML",
        }
        return ext_map.get(ext, "Unknown")

    def index_repository(self, repository_name: str) -> List[FileMetadataResponse]:
        workspace_dir = Path("workspace")
        repo_name = repository_name.split("/")[-1]
        repo_path = workspace_dir / repo_name
        
        if not repo_path.exists():
            raise ValueError(f"Repository {repo_name} not found locally.")

        ignored_dirs = {".git", "venv", "node_modules", "__pycache__", "dist", "build"}
        files_list = []

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(repo_path)
                size = file_path.stat().st_size
                ext = file_path.suffix.lower()
                language = self._get_language(ext)
                
                files_list.append(
                    FileMetadataResponse(
                        path=str(relative_path).replace("\\", "/"),
                        extension=ext,
                        language=language,
                        size=size
                    )
                )
                
        return files_list
