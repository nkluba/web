document.addEventListener("DOMContentLoaded", function () {
    const regionInput = document.getElementById("region-input");
    const regionList = document.getElementById("region-list");

    const stopInput = document.getElementById("stop-input");
    const stopList = document.getElementById("stop-list");

    const submitRegionButton = document.getElementById("submit-region");
    const regionForm = document.getElementById("region-form");

    const stopForm = document.getElementById("stop-form");
    const busList = document.getElementById("bus-list");
    const busListContainer = document.getElementById("bus-list-container");

    const arrivalsContainer = document.getElementById('arrivals-container');

    const clearButton = document.getElementById("clear-button");

    clearButton.addEventListener("click", function () {
        regionInput.value = '';
        stopInput.value = '';

        regionList.innerHTML = '';
        stopList.innerHTML = '';

        busList.innerHTML = '';
        arrivalsContainer.innerHTML = '';
    });

    function clearBusAndArrivals() {
        busList.innerHTML = '';
        arrivalsContainer.innerHTML = '';
    }

    regionInput.addEventListener("change", function () {
        stopInput.value = '';
        clearBusAndArrivals();
    });

    stopInput.addEventListener("change", function () {
        clearBusAndArrivals();
    });

    //get stops when region button is clicked
    submitRegionButton.addEventListener("click", function () {
        const selectedRegion = regionInput.value;

        if (selectedRegion) {
            fetch(`/get_stops?region=${selectedRegion}`)
                .then(response => response.json())
                .then(data => updateStopDropdown(data.stops))
                .catch(error => console.error('Error fetching stops:', error));
        }
    });

    //get user location, query db for all bus routes where stop1 (closest to user location) is before stop2 by sequence
    //so user won't get buses on which he can't ride to the desired stop
    //select closest stop which fits that conditons and query buses
    stopForm.addEventListener("submit", function (event) {
        event.preventDefault();
        const selectedStop = stopInput.value;
        const selectedRegion = regionInput.value;

        if (selectedStop) {
            document.getElementById('spinner').style.display = 'block';
            navigator.geolocation.getCurrentPosition(
                function (position) {
                    const userLatitude = position.coords.latitude;
                    const userLongitude = position.coords.longitude;
                    //get closest stop which fits to the condition described above
                    const closestStopPromise = getClosestStop(userLatitude, userLongitude, selectedStop, selectedRegion);

                    closestStopPromise.then((result) => {
                        const closestStopId = result.closest_stop.stop_id;
                        fetch(`/get_buses?stop=${selectedStop}&region=${selectedRegion}&closest_stop=${closestStopId}`)
                            .then(response => response.json())
                            .then(data => displayBusList(data.buses))
                            .catch(error => console.error('Error fetching buses:', error))
                            .finally(() => {
                                document.getElementById('spinner').style.display = 'none';
                            });
                    }).catch((error) => {
                        console.error('Error getting closest stop:', error);
                    });
                },
                function (error) {
                    console.error('Error getting user location:', error);
                }
            );
        }
    });

    regionInput.addEventListener("input", function () {
        const inputValue = this.value.toLowerCase();
        regionInputValue = inputValue;

        regionList.innerHTML = "";

        fetch(`/get_regions_autocomplete?input=${inputValue}`)
            .then(response => response.json())
            .then(data => {
                if (inputValue === regionInputValue) {
                    data.regions.forEach(region => {
                        const listItem = document.createElement("div");
                        listItem.textContent = region;
                        listItem.addEventListener("click", function () {
                            regionInput.value = region;
                            regionList.innerHTML = "";
                            //fetchStopsAndUpdateDropdown();
                        });
                        regionList.appendChild(listItem);
                    });
                }
            })
            .catch(error => console.error('Error fetching regions:', error));
    });

    let selectedStopId;


    stopInput.addEventListener("input", function () {
        const inputValue = this.value.toLowerCase();
        const selectedRegion = regionInput.value;
        stopInputValue = inputValue;

        stopList.innerHTML = "";

        fetch(`/get_stops?region=${selectedRegion}&stop=${inputValue}`)
            .then(response => response.json())
            .then(data => {
                if (inputValue === stopInputValue) {
                    data.stops.forEach(stop => {
                        const listItem = document.createElement("div");
                        listItem.textContent = stop.stop_name;
                        listItem.addEventListener("click", function () {
                            stopInput.value = stop.stop_name;
                            stopList.innerHTML = "";
                            selectedStopId = stop.stop_name;
                        });
                        stopList.appendChild(listItem);
                    });
                }
            })
            .catch(error => console.error('Error fetching stops:', error));
    });

    regionInput.addEventListener("focus", function () {
        regionList.innerHTML = "";
    });

    regionForm.addEventListener("submit", function (event) {
        event.preventDefault();
    });

    function updateRegionDropdown(regions) {
        regionList.innerHTML = "";
        regions.forEach(region => {
            const listItem = document.createElement("div");
            listItem.textContent = region;
            listItem.addEventListener("click", function () {
                regionInput.value = region;
                regionList.innerHTML = "";
                //fetchStopsAndUpdateDropdown();
            });
            regionList.appendChild(listItem);
        });
    }

    function updateStopDropdown(stops) {
        stopList.innerHTML = "";

        stops.forEach(stop => {
            const listItem = document.createElement("div");
            listItem.textContent = stop.stop_name;
            listItem.addEventListener("click", function () {
                stopInput.value = stop.stop_name;
                stopList.innerHTML = "";
                const selectedStopId = this.dataset.stopId;
            });
            stopList.appendChild(listItem);
        });
    }

    //sort by route_short_name, set service_id (for timetable per week), arrival and departure times for each bus
    function displayBusList(buses) {
        const uniqueBusesMap = new Map();

        buses.forEach((bus) => {
            const tripLongName = bus.trip_long_name;
            if (uniqueBusesMap.has(tripLongName)) {
                uniqueBusesMap.get(tripLongName).push(bus);
            } else {
                uniqueBusesMap.set(tripLongName, [bus]);
            }
        });

        const sortedUniqueBuses = [...uniqueBusesMap.values()].sort((a, b) => {
            const numA = parseInt(a[0].route_short_name.replace(/\D/g, ''), 10);
            const numB = parseInt(b[0].route_short_name.replace(/\D/g, ''), 10);
            return numA - numB;
        });

        busList.innerHTML = "";

        sortedUniqueBuses.forEach((buses) => {
            const busButton = document.createElement("button");
            const firstBus = buses[0];
            busButton.textContent = `${firstBus.route_short_name} - ${firstBus.trip_long_name}`;

            busButton.closestStop = firstBus.closest_stop;
            busButton.serviceID = buses.map(bus => bus.service_id);
            busButton.bDeparture = buses.map(bus => bus.b_departure);
            busButton.bArrival = buses.map(bus => bus.b_arrival);

            busList.appendChild(busButton);
        });
    }

    function getClosestStop(userLatitude, userLongitude, selectedStop, selectedRegion) {
        return fetch(`/get_closest_stop?longitude=${userLongitude}&latitude=${userLatitude}&selected_stop=${selectedStop}&stop_area=${selectedRegion}`)
            .then(response => response.json())
            .catch(error => {
                console.error('Error getting closest stop:', error);
                throw error;
            });
    }

    busListContainer.addEventListener("click", function (event) {
        const target = event.target;

        if (target.tagName === "BUTTON") {
            displayBusTimes(target);
        }
    });

    //get top 5 closest arrivals for today and (if not sufficient) tomorrow
    function displayBusTimes(busButton) {
        arrivalsContainer.innerHTML = "";

        const params = new URLSearchParams({
            service_id: busButton.serviceID,
            bDeparture: busButton.bDeparture,
            bArrival: busButton.bArrival,
        });

        fetch(`/get_timetable?${params.toString()}`)
            .then(response => response.json())
            .then(timetableData => {
                timetableData.forEach((arrival, index) => {
                    const arrivalItem = document.createElement("div");
                    arrivalItem.innerHTML = `
        <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${busButton.textContent}</h5>
                    <p class="card-subtitle mb-2 text-muted">
                        Departure Time From Closest Stop 
                        (<span class="fw-bold text-primary">${busButton.closestStop}</span>): 
                        <span class="fw-bold text-primary">${arrival.bDeparture}</span>
                    </p>
                    <p class="card-subtitle mb-2 text-muted">
                        Arrival Time to Destination: 
                        <span class="fw-bold text-primary">${arrival.bArrival}</span>, 
                        Day: <span class="fw-bold text-primary">${arrival.day}</span>
                    </p>
                </div>
            </div>
        `;
                    arrivalsContainer.appendChild(arrivalItem);
                });
            })
            .catch(error => console.error('Error:', error));
    }
});