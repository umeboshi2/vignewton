<div class="admin-list-transfers-view">
  <% ttypes = am.get_txn_types() %>
  <% transactions = am.get_all_transactions() %>
  <% dtformat = '%b %d %Y - %H:%M:%S' %>
  %for txn in transactions:
  <div class="listview-header">
    <p>${txn.created.strftime(dtformat)} - ${ttypes[txn.type_id]} </p>
  </div>
  <div class="listview-list">
    <div class="listview-list-entry">
      <table>
	<tr><th>Account</th><th>Amount</th></tr>
        %for xfer in txn.transfers:
	<tr>
	  <td>${xfer.account.name}</td>
	  <td>${xfer.amount}</td>
	</tr>
	%endfor
      </table>
    </div>
  </div>
  %endfor
</div>

