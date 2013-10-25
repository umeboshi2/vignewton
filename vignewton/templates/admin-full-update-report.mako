<div class="admin-full-update-report-view">
  <% dtformat = '%b %d %Y - %H:%M:%S' %>
  <div class="listview-header">
    <p>Update Report</p>
  </div>
  <div class="listview-list">
    %for r in reports:
    <% c = r.content %>
    <div class="listview-list-entry">
      Created:  ${r.created.strftime(dtformat)}<br>
      Schedule Updated: ${c['games_updated']}<br>
      Odds Updated: ${c['odds_updated']}<br>
      <% bets = c['determined'] %>
      <% undetermined = [b for b in bets if b is None] %>
      <% determined = [b for b in bets if b is not None] %>
      %if undetermined:
      Unable to determine ${len(undetermined)} bets.<br>
      %endif
      %if determined:
      Determined ${len(determined)} bets.<br>
      %endif
      %if not bets:
      No Pending Bets.
      %endif
    </div>
    %endfor
  </div>
</div>

