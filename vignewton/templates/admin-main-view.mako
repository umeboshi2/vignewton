<div class="admin-main-view">
  <% dtformat = '%b %d %Y - %H:%M:%S' %>
  <% mkurl = request.route_url %>
  <% route = 'admin_updatedb' %>
  <% from datetime import timedelta, datetime %>
  <% now = datetime.now() %>
  <% two_days = timedelta(days=2) %>
  <% one_day = timedelta(days=1) %>
  <% ten_seconds = timedelta(seconds=10) %>
  <div class="listview-header">
    Main Admin View
  </div>
  <div class="listview-list">
    %if not games.query().all():
    <div class="listview-list-entry">
      <% url = mkurl(route, context='games', id='cash') %>
      <p>
	There is no Game Schedule. 
	<a class="action-button" href="${url}">
	  Update
	</a>
      </p>
    </div>
    %else:
    <div class="listview-list-entry">
      <% latest = games.get_latest_scored_game() %>
      <% url = mkurl(route, context='games', id='cash') %>
      <h4>Latest Scored Game</h4>
      ${latest.start.strftime(dtformat)}<br>
      ${latest.summary}
      %if now - latest.start > two_days:
      <a class="action-button" href="${url}">
	Update
      </a>
      %endif
    </div>
    %endif
    %if not odds.query().all(): 
    <div class="listview-list-entry">
      <% url = mkurl(route, context='odds', id='cash') %>
      <p>
	There are no odds in database.
	<a class="action-button" href="${url}">
	  Update
	</a>
      </p>
    </div>
    %else:
    <div class="listview-list-entry">
      <% latest = games.get_latest_scored_game() %>
      <% url = mkurl(route, context='games', id='cash') %>
      <h4>Latest Scored Game</h4>
      ${latest.start.strftime(dtformat)}<br>
      ${latest.summary}
      %if now - latest.start > two_days:
      <a class="action-button" href="${url}">
	Update
      </a>
      %endif
    </div>
    %endif
 </div>
</div>

