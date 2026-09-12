// Pick Em client-side logic: who's picking, their picks, lock-in submission.
// ponytail: no backend yet — submit() posts to a placeholder endpoint and
// fails gracefully. Wire this up once the Python side exists.

(function () {
  var STORAGE_KEY = 'pickem_user';
  var SUBMIT_URL = 'submit-picks.py'; // placeholder — doesn't exist yet

  var rows = document.querySelectorAll('.pickem-row');
  var heading = document.getElementById('pickem-heading');
  var lockBtn = document.getElementById('pickem-lock-btn');
  var resetPicksBtn = document.getElementById('pickem-reset-picks-btn');
  var resetUserLink = document.getElementById('pickem-reset-user-link');
  var status = document.getElementById('pickem-status');
  var fixtureGrid = document.getElementById('fixture-grid');

  var selectedUser = localStorage.getItem(STORAGE_KEY) || null;
  var locked = false;

  function render() {
    rows.forEach(function (row) {
      var isSelected = row.dataset.user === selectedUser;
      row.classList.toggle('selected', isSelected);
      row.classList.toggle('locked', locked);
    });
    heading.textContent = selectedUser ? 'Who ya got, ' + selectedUser + '?' : 'Who ya got?';
    lockBtn.disabled = !selectedUser || locked;
  }

  rows.forEach(function (row) {
    row.addEventListener('click', function () {
      if (locked) return;
      selectedUser = row.dataset.user;
      localStorage.setItem(STORAGE_KEY, selectedUser);
      render();
    });
  });

  function resetPicks() {
    fixtureGrid.querySelectorAll('input[type="radio"]').forEach(function (input) {
      input.checked = false;
      input.disabled = false;
    });
    locked = false;
    status.textContent = '';
    render();
  }

  function resetUser() {
    selectedUser = null;
    localStorage.removeItem(STORAGE_KEY);
    resetPicks();
  }

  resetPicksBtn.addEventListener('click', resetPicks);
  resetUserLink.addEventListener('click', function (e) {
    e.preventDefault();
    resetUser();
  });

  function collectPicks() {
    var picks = [];
    var groups = {};
    fixtureGrid.querySelectorAll('input[type="radio"]:checked').forEach(function (input) {
      var label = input.closest('.fixture-team');
      groups[input.name] = label.querySelector('.name').textContent;
    });
    for (var fixture in groups) {
      picks.push({ fixture: fixture, pick: groups[fixture] });
    }
    return picks;
  }

  function submitPicks(payload) {
    return fetch(SUBMIT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  }

  lockBtn.addEventListener('click', function () {
    var picks = collectPicks();
    var totalFixtures = fixtureGrid.querySelectorAll('.fixture-card').length;
    if (picks.length < totalFixtures) {
      status.textContent = 'Pick every match before locking in (' + picks.length + '/' + totalFixtures + ' so far).';
      return;
    }

    var payload = { user: selectedUser, picks: picks };
    console.log('Pick Em submission (client-side only for now):', payload);

    locked = true;
    render();
    fixtureGrid.querySelectorAll('input[type="radio"]').forEach(function (input) {
      input.disabled = true;
    });
    status.textContent = 'Picks locked in for ' + selectedUser + '. Saving to the server...';

    submitPicks(payload)
      .then(function (res) {
        if (!res.ok) throw new Error('server responded ' + res.status);
        status.textContent = 'Picks locked in and saved for ' + selectedUser + '.';
      })
      .catch(function () {
        status.textContent = 'Picks locked in for ' + selectedUser + ' (saved locally — server sync isn’t wired up yet).';
      });
  });

  render();
})();
