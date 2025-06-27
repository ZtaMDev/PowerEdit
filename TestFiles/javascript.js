class GitHubUser {
  constructor(username) {
    this.username = username;
    this.profile = null;
    this.repos = [];
  }
 
  async fetchProfile() {
    try {
      const res = await fetch(`https://api.github.com/users/${this.username}`);
      if (!res.ok) throw new Error('Usuario no encontrado');
      this.profile = await res.json();
    } catch (error) {
      throw error; 
    }
  }

  async fetchRepos() {
    try {
      const res = await fetch(`https://api.github.com/users/${this.username}/repos`);
      if (!res.ok) throw new Error('No se pudieron obtener los repositorios');
      this.repos = await res.json();
    } catch (error) {
      throw error;
    }
  }
}

const app = (() => {
  const form = document.querySelector('#searchForm');
  const input = document.querySelector('#usernameInput');
  const userInfoDiv = document.querySelector('#userInfo');
  const reposList = document.querySelector('#reposList');
  const errorDiv = document.querySelector('#error');

  const clearDisplay = () => {
    userInfoDiv.innerHTML = '';
    reposList.innerHTML = '';
    errorDiv.textContent = '';
  };

  const renderUser = (user) => {
    userInfoDiv.innerHTML = `
      <img src="${user.profile.avatar_url}" alt="${user.username}" width="100" />
      <h2>${user.profile.name || user.username}</h2>
      <p>${user.profile.bio || 'Sin bio disponible'}</p>
      <p>Seguidores: ${user.profile.followers} | Siguiendo: ${user.profile.following}</p>
      <a href="${user.profile.html_url}" target="_blank">Ver perfil en GitHub</a>
    `;
  };

  const renderRepos = (repos) => {
    if (repos.length === 0) {
      reposList.innerHTML = '<p>Este usuario no tiene repositorios públicos.</p>';
      return;
    }

    reposList.innerHTML = repos
      .map(repo => `
        <li>
          <a href="${repo.html_url}" target="_blank">${repo.name}</a>
          <p>${repo.description || 'Sin descripción'}</p>
          <p>⭐ ${repo.stargazers_count} | Forks: ${repo.forks_count}</p>
        </li>
      `)
      .join('');
  };

  const showError = (msg) => {
    errorDiv.textContent = msg;
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearDisplay();
    const username = input.value.trim();

    if (!username) {
      showError('Por favor, ingresa un nombre de usuario.');
      return;
    }

    const user = new GitHubUser(username);

    try {
      await user.fetchProfile();
      renderUser(user);
      await user.fetchRepos();
      renderRepos(user.repos);
    } catch (error) {
      showError(error.message);
    }
  });

  return {
    // Podrías exponer métodos o propiedades si quieres
  };
})();
