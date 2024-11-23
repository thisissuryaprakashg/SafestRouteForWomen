mapboxgl.accessToken = "pk.eyJ1Ijoic3VyeWFwcmFrYXNoZyIsImEiOiJjbTM0b3hmcXUwMjhoMmxzOXMyZ3QzZzV3In0.YhhvI2ASeIL5lHht44Nx5Q";

navigator.geolocation.getCurrentPosition(successLocation, errorLocation, {
  enableHighAccuracy: true,
});

let virtualLocation; // Simulated user location

function successLocation(position) {
  const startLocation = [position.coords.longitude, position.coords.latitude];
  virtualLocation = startLocation; // Set initial virtual location
  setupMap(startLocation);
}

function errorLocation() {
  const fallbackLocation = [-2.24, 53.48]; // Default location
  virtualLocation = fallbackLocation; // Set initial virtual location
  setupMap(fallbackLocation);
}

function setupMap(center) {
  const map = new mapboxgl.Map({
    container: "map",
    style: "mapbox://styles/mapbox/streets-v11",
    center: center,
    zoom: 15,
  });

  const nav = new mapboxgl.NavigationControl();
  map.addControl(nav);

  const directions = new MapboxDirections({
    accessToken: mapboxgl.accessToken,
    unit: "metric",
    profile: "mapbox/driving",
    alternatives: true,
  });

  map.addControl(directions, "top-left");

  let steps = [];
  let userMarker = new mapboxgl.Marker({ color: "blue" }).setLngLat(center).addTo(map);

  // Update user marker position
  function updateUserMarker(coords) {
    virtualLocation = coords;
    userMarker.setLngLat(coords);
    map.setCenter(coords);
  }

  // Listen for route selection
  directions.on("route", (e) => {
    if (e.route && e.route.length > 0) {
      const route = e.route[0];
      steps = route.legs[0].steps.map((step) => ({
        location: step.maneuver.location,
        instruction: step.maneuver.instruction,
        streetName: step.name, // Extract the street name
      }));

      // Extract unique street names
      const streetNames = new Set(steps.map((step) => step.streetName).filter(Boolean)); // Filter out undefined names

      console.log("Route steps:", steps);
      console.log("Street Names:", Array.from(streetNames)); // Convert Set to Array for display

      displayStreetNames(Array.from(streetNames)); // Display street names in UI
    }
  });

  // Check proximity to steps
  function checkProximity() {
    const thresholdDistance = 50; // in meters
    const matchingStep = steps.find((step) => {
      const distance = haversineDistance(virtualLocation, step.location);
      return distance < thresholdDistance;
    });

    if (matchingStep) {
      displayInstruction(matchingStep.instruction);
      steps = steps.filter((step) => step !== matchingStep); // Remove matched step
    }
  }

  // Simulate movement
  function move(dx, dy) {
    const [lon, lat] = virtualLocation;
    const newLocation = [lon + dx, lat + dy];
    updateUserMarker(newLocation);
    checkProximity();
  }

  // Event listeners for arrow controls
  document.getElementById("up").addEventListener("click", () => move(0, 0.001));
  document.getElementById("down").addEventListener("click", () => move(0, -0.001));
  document.getElementById("left").addEventListener("click", () => move(-0.001, 0));
  document.getElementById("right").addEventListener("click", () => move(0.001, 0));
}

// Calculate distance between two coordinates (Haversine formula)
function haversineDistance(coord1, coord2) {
  const R = 6371000; // Radius of the Earth in meters
  const toRad = (angle) => (angle * Math.PI) / 180;

  const lat1 = toRad(coord1[1]);
  const lat2 = toRad(coord2[1]);
  const deltaLat = toRad(coord2[1] - coord1[1]);
  const deltaLon = toRad(coord2[0] - coord1[0]);

  const a =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

// Display turn-by-turn instruction
function displayInstruction(instruction) {
  let instructionDiv = document.getElementById("instruction");
  if (!instructionDiv) {
    instructionDiv = document.createElement("div");
    instructionDiv.id = "instruction";
    instructionDiv.style.position = "absolute";
    instructionDiv.style.top = "20px";
    instructionDiv.style.left = "50%";
    instructionDiv.style.transform = "translateX(-50%)";
    instructionDiv.style.padding = "10px";
    instructionDiv.style.backgroundColor = "rgba(0, 0, 0, 0.8)";
    instructionDiv.style.color = "white";
    instructionDiv.style.borderRadius = "5px";
    instructionDiv.style.zIndex = "9999";
    instructionDiv.style.fontSize = "16px";
    instructionDiv.style.maxWidth = "80%";
    instructionDiv.style.textAlign = "center";
    document.body.appendChild(instructionDiv);
  }
  instructionDiv.textContent = instruction;
}

// Display list of street names
function displayStreetNames(streetNames) {
  let streetListDiv = document.getElementById("street-list");
  if (!streetListDiv) {
    streetListDiv = document.createElement("div");
    streetListDiv.id = "street-list";
    streetListDiv.style.position = "absolute";
    streetListDiv.style.top = "80px";
    streetListDiv.style.left = "50%";
    streetListDiv.style.transform = "translateX(-50%)";
    streetListDiv.style.padding = "10px";
    streetListDiv.style.backgroundColor = "rgba(255, 255, 255, 0.8)";
    streetListDiv.style.color = "black";
    streetListDiv.style.borderRadius = "5px";
    streetListDiv.style.zIndex = "9999";
    streetListDiv.style.fontSize = "14px";
    streetListDiv.style.maxWidth = "80%";
    streetListDiv.style.textAlign = "center";
    document.body.appendChild(streetListDiv);
  }

  streetListDiv.innerHTML = `
    <h3>Street Names:</h3>
    <ul>
      ${streetNames.map((name) => `<li>${name}</li>`).join("")}
    </ul>
  `;
}
