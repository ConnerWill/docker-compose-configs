const FAVORITES_KEY = 'guncad_favorites';

function getFavorites() {
	try {
		return JSON.parse(localStorage.getItem(FAVORITES_KEY)) || [];
	} catch {
		return [];
	}
}

function saveFavorites(favs) {
	localStorage.setItem(FAVORITES_KEY, JSON.stringify(favs));
}

function clearFavorites() {
	localStorage.setItem(FAVORITES_KEY, []);
}

function toggleFavorite(id) {
	let favs = getFavorites();
	if (favs.includes(id)) {
		favs = favs.filter(x => x !== id);
	} else {
		favs.push(id);
	}
	saveFavorites(favs);
	updateFavoriteUI();
}

function updateFavoriteUI() {
	const favs = getFavorites();
	document.querySelectorAll('.favorite-toggle').forEach(el => {
		const id = el.dataset.releaseId;
		if (favs.includes(id)) {
			el.classList.add('favorited');
		} else {
			el.classList.remove('favorited');
		}
	});
	document.querySelectorAll('.favorite-indicator').forEach(el => {
		const id = el.dataset.releaseId;
		if (favs.includes(id)) {
			el.classList.add('favorited');
		} else {
			el.classList.remove('favorited');
		}
	});
}

async function loadFavorites() {
	const container = document.getElementById('favorites-target');
	if (!container) return;

	// Handle the case where there are no favorites
	// This can happen when this is called on the front page after the user
	// trashes all of their favorites, so we need this section.
	const favs = getFavorites();
	if (!favs.length) {
		container.classList.remove('favorites-populated');
		container.innerHTML = '';
		return;
	}

	// While we wait for HOTW, display the placeholder card the template
	// should have provided
	container.classList.add('favorites-populated');
	const placeholder = container.firstElementChild?.cloneNode(true);
	if (placeholder) {
		container.replaceChildren();
		for (let i = 0; i < favs.length; i++) {
			container.appendChild(placeholder.cloneNode(true));
		}
	}

	// HOTW
	try {
		const resp = await fetch('/favorites/render/', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/x-www-form-urlencoded',
				'X-Requested-With': 'XMLHttpRequest',
				'X-CSRFToken': getCSRFToken(), // helper below
			},
			body: new URLSearchParams(favs.map(id => ['ids[]', id])),
		});

		if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
		const html = await resp.text();
		container.innerHTML = html;
		// Importantly, we should re-run the favorite UI init so we, yaknow, put
		// bookmark icons on all the user's favorites
		updateFavoriteUI();
	} catch (err) {
		console.error('Error loading bookmarks:', err);
		container.innerHTML = '<div class="helpblurb"><h1>Uh... Fuck</h1><p>Encountered an error while loading bookmarks. May wanna clear them out with the little trash can up there or try again later.</p><p>See the console for more details.</p></div>';
	}
}

function getCSRFToken() {
	const name = 'csrftoken=';
	return document.cookie
		.split('; ')
		.find(row => row.startsWith(name))
		?.slice(name.length) || '';
}

function initFavorites() {
	updateFavoriteUI();
	loadFavorites();
}

document.addEventListener('DOMContentLoaded', () => {
	// Handler for Favorite buttons
	document.body.addEventListener('click', e => {
		const el = e.target.closest('.favorite-toggle');
		if (!el) return;
		e.preventDefault();
		const id = el.dataset.releaseId;
		toggleFavorite(id);
		updateFavoriteUI();
	});
	// Handler for clear favorites button
	document.body.addEventListener('click', e => {
		const el = e.target.closest('.favorite-clear');
		if (!el) return;
		e.preventDefault();
		clearFavorites();
		initFavorites();
	});
});
document.addEventListener('DOMContentLoaded', initFavorites);
window.addEventListener('pageshow', event => {
	if (event.persisted) initFavorites();
});
