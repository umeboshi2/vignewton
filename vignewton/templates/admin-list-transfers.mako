<div class="admin-list-transfers-view">
  <div class="listview-header">
    <p>Pending Bets</p>
  </div>
  <table>
    <tr><th>Type</th><th>Account</th><th>Amount</th></tr>
  %for xfer in transfers:
  <div class="listview-list">
    <div class="listview-list-entry">
      <tr>
	<td>${xfer.type.name}</td>
	<td>${xfer.account.name}</td>
	<td>${xfer.amount}</td>
      </tr>
    </div>
  </div>
  %endfor
  </table>
</div>

