<div class="main-nfl-teams-view">
  <div class="view-header">
    <p>NFL</p>
  </div>
  <div class="view-list">
    NFL Teams
    %for team in teams:
    <div class="view-list-entry">
      <% tval = '%s %s' % (team.city, team.name) %>
      <% url = request.route_url('vig_nflteams', context='viewteam', id=team.id) %>
      <a href="${url}">${tval}</a>(${team.conference}-${team.region})
    </div>
    %endfor
  </div>
</div>
