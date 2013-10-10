<div class="admin-determine-bets-view">
  <% dtformat = '%b %d %Y - %H:%M:%S' %>
  <div class="listview-header">
    <p>Closed Bets</p>
  </div>
  <div class="listview-list">
    %for cb in clist:
    <div class="listview-list-entry">
      %if cb is not None:
        ${cb.amount}, ${cb.status}
      %else:
        Bet could not be determined yet.
      %endif
    </div>
    %endfor
  </div>
</div>

