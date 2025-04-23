document.getElementById("predict-form").addEventListener("submit", async function (e) {
    e.preventDefault();
  
    const year = document.getElementById("year").value;
    const round = document.getElementById("round").value;
  
    // 🔁 MOCKED for now — you’ll later point this to your backend
    const mockResult = ["max_verstappen", "charles_leclerc", "fernando_alonso"];
  
    // Simulate "fetch" call
    await new Promise(resolve => setTimeout(resolve, 500)); // fake delay
  
    // Display result
    const resultDiv = document.getElementById("prediction-result");
    const podiumList = document.getElementById("podium-list");
  
    resultDiv.classList.remove("hidden");
    podiumList.innerHTML = "";
  
    mockResult.forEach((driver, idx) => {
      const li = document.createElement("li");
      li.textContent = `#${idx + 1}: ${driver.replace("_", " ").toUpperCase()}`;
      podiumList.appendChild(li);
    });
  });
  