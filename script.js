document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('.add-expenditure-form');

  form.addEventListener('submit', function (event) {
    event.preventDefault();

    const purpose = document.getElementById('purpose').value;
    const sum = document.getElementById('sum').value;
    const date = document.getElementById('date').value;
    const categorySelect = document.getElementById('category');
    const category = categorySelect.options[categorySelect.selectedIndex].text; // Retrieve the selected category

    // Create a data object to send to the server
    const data = {
      purpose: purpose,
      sum: sum,
      date: date,
      category: category
    };

    // Send the data to the server
    sendDataToServer(data);
  });

  function sendDataToServer(data) {
    // Make a POST request to the server
    fetch('/add-expense', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      console.log('Expense added successfully:', data);
      // You can perform any additional actions here after successfully adding the expense
      // For example, update the UI or display a success message
    })
    .catch(error => {
      console.error('Error adding expense:', error);
      // Handle errors here, such as displaying an error message to the user
    });
  }
});
