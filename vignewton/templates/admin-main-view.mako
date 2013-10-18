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
  <% no_games = False %>
  <div class="listview-list">
    %if not games.query().all():
    <div class="listview-list-entry">
      <% url = mkurl(route, context='games', id='cash') %>
      <% no_games = True %>
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
      <strong>Latest Scored Game</strong>
      ${latest.start.strftime(dtformat)}<br>
      ${latest.summary}
      %if now - latest.start > two_days:
      <a class="action-button" href="${url}">
	Update
      </a>
      %endif
    </div>
    %endif
    %if not no_games:
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
      <% latest = odds.oddscache.get_latest_content() %>
      <% url = mkurl(route, context='games', id='cash') %>
      <strong>Latest Odds Retrieval</strong>
      ${latest.retrieved.strftime(dtformat)}<br>
      %if now - latest.retrieved > one_day:
      <a class="action-button" href="${url}">
	Update
      </a>
      %endif
    </div>
    %endif
    %else:
    <div class="listview-list-entry">
      There can be no odds without games.
    </div>
    %endif
    %if bets.get_all_bets():
    <div class="listview-list-entry">
      There are pending bets.
    </div>
    %else:
    <div class="listview-list-entry">
      There are no pending bets.
    </div>
    %endif
    <% balance = bets.accounts.get_balance(bets.accounts.inthewild.id) %>
    %if balance.balance == 0:
    <div class="listview-list-entry">
      There is no money in the system!
    </div>
    %else:
    <div class="listview-list-entry">
      There is $${-balance.balance} in the system.
    </div>
    %endif
 </div>
</div>

