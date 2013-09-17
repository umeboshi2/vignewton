<div class="view-nfl-team">
  <% tval = '%s %s' % (team.city, team.name) %>
  <div class="view-header">
    <p>NFL ${tval}</p>
  </div>
  <div class="view-list">
    Former ${team.name} Games
    %for game in games:
    <div class="view-list-entry">
      <% url = request.route_url('vig_nflteams', context='viewteam', id=team.id) %>
      %if game.start < now:
		       <a href="${url}">${game.summary}</a>(${game.start.isoformat()})
      %endif
    </div>
    %endfor
  </div>
  <div class="view-list">
    Scheduled ${team.name} Games
    %for game in games:
    <div class="view-list-entry">
      <% url = request.route_url('vig_nflteams', context='viewteam', id=team.id) %>
      %if game.start >= now:
		       <a href="${url}">${game.summary}</a>(${game.start.isoformat()})
      %endif
    </div>
    %endfor
  </div>
</div>
