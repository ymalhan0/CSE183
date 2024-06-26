"use strict";

let app = {};

let init = (app) => {

    app.data = {

        search_parts: "",

        trade_items: [],
        curr_user_trade_items: [],
        curr_user_parts_have: [],
        curr_user_parts_seeking: [],
        current_user: "",
        city_list: [],
        plane_list: [],
        sorted_plane_list: [],
        selected_city_a: '',
        selected_city_b: '',
        allCityInfo: {},
        allPlaneInfo: {},

        distance_result: '',
        distance_result_cities: '',
        distance_result_classes: '',
        distance_result_class_string: '',
        distance_result_viable_planes: '',
        distance_result_same: '',
        sortedViablePlanes: [],

        flight_planner_items: [],
        planner_city_a_field: "",
        planner_city_b_field: "",
        total_distance: '',
        planner_plane_field: "",
        planner_result: "",

        planner_result_profit: '',
        planner_result_flight_time: '',
        planner_result_profitph: '',
        planner_result_total_distance: '',
        planner_result_longest_leg: '',

    };

    app.enumerate = (a) => {
        let k = 0;
        a.map((e) => { e._idx = k++; });
        return a;
    };

    app.methods = {

        // search through have parts
        search(query) {
            //console.log(query)
            for (let x = 0; x < query.length; x++) {
                //for (let y = 0; y < query[x].part_name.length; y++) {
                //console.log(query[x].part_name.includes(app.vue.search_parts))
                if (query[x].part_name.toLowerCase().startsWith(app.vue.search_parts.toLowerCase())) {
                    return true;
                }
                //}
            }
        },

        // clear search bar and refresh table
        clear_search() {
            axios.get("/companion/get_entries")
                .then(function (result) {
                    app.vue.search_parts = ""
                    app.methods.get_entries()
                })
        },
        // get all trade item entries
        get_entries() {
            axios.get("/companion/get_entries").then(function (response) {
                app.data.trade_items = app.enumerate(response.data.rows)
                app.methods.get_current_user()
            })
        },
        // get the current user's entries
        get_curr_user_entry() {
            axios.get("/companion/get_curr_user_entry").then(function (response) {
                app.data.curr_user_trade_items = app.enumerate(response.data.rows)
            })

            axios.get("/companion/get_curr_user_parts").then(function (response2) {
                if ((response2.data.have != null) && (response2.data.seeking != null)) {
                    app.data.curr_user_parts_have = app.enumerate(response2.data.have)
                    app.data.curr_user_parts_seeking = app.enumerate(response2.data.seeking)
                }
            })
        },
        // remove a part entry
        remove_part(id) {
            axios.get("/companion/remove_part", { params: { part_id: id } }).then(function (response) {
                app.methods.get_curr_user_entry()
                app.methods.get_entries()
            })
        },
        // for offers and reservations
        swap_reservation(id) {
            axios.get("/companion/swap_reservation", { params: { part_id: id } }).then(function (response) {
                if (response.data.error) {
                    // handle the error, you can show a message to the user
                    console.log(response.data.error);
                } else {
                    app.data.offers = response.data.offers;
                    app.data.reservations = response.data.reservations;
                    app.methods.get_entries()
                }
            })
        },
        // get current user
        get_current_user() {
            axios.get("/companion/get_current_user").then(function (response) {
                app.data.current_user = response.data.current_user
            })
        },

        // Functions for Distance Calculator:

        // Grabs the json file as an object and generates our app.data
        // city list
        generate_city_list() {
            axios.get("/companion/get_cities").then(function (response) {
                let cityObj = response.data.cities
                let planeObj = response.data.planes
                for (let cityIndex in cityObj) {
                    app.data.city_list.push(cityObj[cityIndex].city)

                    let data = cityObj[cityIndex]
                    app.data.allCityInfo[cityObj[cityIndex].city] = data
                }
                for (let planeIndex in planeObj) {
                    app.data.plane_list.push(planeObj[planeIndex].plane)

                    let plane_data = planeObj[planeIndex]
                    app.data.allPlaneInfo[planeObj[planeIndex].plane] = plane_data
                }
                app.data.sorted_plane_list = app.data.plane_list.sort()
            })

        },

        // Main function, takes two strings (city names) and checks
        // if they are in the list of cities. Returns a string stating
        // the distance, and a list of viable planes for the route.
        distanceCalc(a, b) {
            if (a != b) {
                // calculate distance
                var dist = app.methods.distance(a, b)

                var viablePlanes = []
                var minClass = Math.min(parseInt(app.data.allCityInfo[a].class), parseInt(app.data.allCityInfo[b].class))

                // iterate through all the planes
                for (const [plane, data] of Object.entries(app.data.allPlaneInfo)) {

                    let rangeArray = app.methods.upgradeRange(plane)

                    // if the plane's range is smaller or equal to the distance
                    if (app.data.allPlaneInfo[plane].range >= dist && parseInt(app.data.allPlaneInfo[plane].class) <= minClass) {
                        let pushable = "".concat(plane)
                        viablePlanes.push(pushable)
                    } else if (rangeArray[1] >= dist && parseInt(app.data.allPlaneInfo[plane].class) <= minClass) {
                        let pushable = "".concat(plane)
                        let pushable2 = pushable.concat(" (Lvl 1 Range Upgrade)")
                        viablePlanes.push(pushable2)
                    } else if (rangeArray[2] >= dist && parseInt(app.data.allPlaneInfo[plane].class) <= minClass) {
                        let pushable = "".concat(plane)
                        let pushable2 = pushable.concat(" (Lvl 2 Range Upgrade)")
                        viablePlanes.push(pushable2)
                    } else if (rangeArray[3] >= dist && parseInt(app.data.allPlaneInfo[plane].class) <= minClass) {
                        let pushable = "".concat(plane)
                        let pushable2 = pushable.concat(" (Lvl 3 Range Upgrade)")
                        viablePlanes.push(pushable2)
                    } else if (rangeArray[4] >= dist && parseInt(app.data.allPlaneInfo[plane].class) <= minClass) {
                        let pushable = "".concat(plane)
                        let pushable2 = pushable.concat(" (Lvl 4 Range Upgrade) [VIP]")
                        viablePlanes.push(pushable2)
                    }
                }

                if (viablePlanes.length === 0) {
                    viablePlanes.push("None");
                }

            } else if (a === b) {
                app.data.distance_result_same = `Sorry, you cannot fly from ${a} back to ${b}! Please select another city.`
                return

            }
            // below is variables to store data/strings displayed in html
            app.data.distance_result_same = ''

            app.data.distance_result_cities = `The distance between ${a} and ${b} is`
            app.data.distance_result = `${dist} miles.`

            app.data.distance_result_class_string = `This route is limited to`
            app.data.distance_result_classes = `class ${minClass} planes and below.`

            app.data.distance_result_viable_planes = `The viable planes for this route are:`
            // array of sorted planes
            app.data.sortedViablePlanes = viablePlanes.sort()
        },

        // Calculates the distance between the two cities, pulls coordinates from 
        // the list of cities and uses flooring to match the game's calculations.
        distance(a, b) {
            return (Math.floor(Math.sqrt(Math.pow(app.data.allCityInfo[b].x - app.data.allCityInfo[a].x, 2) + Math.pow(app.data.allCityInfo[b].y - app.data.allCityInfo[a].y, 2))) * 4);
        },

        // Calculates all the possible range upgrades for the given plane, and
        // returns a list of all of them. References plane list.
        upgradeRange(plane) {
            let rangeArray = [];
            // Add the original range first
            rangeArray.push(app.data.allPlaneInfo[plane].range)

            // Then add all the upgraded values
            rangeArray.push(Math.round(parseInt(app.data.allPlaneInfo[plane].range) + (parseInt(app.data.allPlaneInfo[plane].range) * 0.05)))
            rangeArray.push(Math.round(parseInt(app.data.allPlaneInfo[plane].range) + (parseInt(app.data.allPlaneInfo[plane].range) * 0.10)))
            rangeArray.push(Math.round(parseInt(app.data.allPlaneInfo[plane].range) + (parseInt(app.data.allPlaneInfo[plane].range) * 0.15)))
            rangeArray.push(Math.round(parseInt(app.data.allPlaneInfo[plane].range) + (parseInt(app.data.allPlaneInfo[plane].range) * 0.20)))
            return rangeArray
        },

        // get all flight planner entries
        get_flight_planner_entries() {
            axios.get("/companion/get_planner").then(function (response) {
                app.data.flight_planner_items = app.enumerate(response.data.rows)
                app.methods.generate_trip_info()
            })
        },

        // Builds a url for the delete and edit buttons in the flight planner
        build_url(page, id) {
            return "/" + page + "/" + id
        },

        // Adds a leg to the planner by calling controller
        add_leg() {
            axios.get("/companion/add_leg", { params: { citya: app.data.planner_city_a_field, cityb: app.data.planner_city_b_field } }).then(function (response) {
                app.methods.get_flight_planner_entries()
                // Swap inputs
                app.data.planner_city_a_field = app.data.planner_city_b_field
                app.data.planner_city_b_field = ''
            })
        },

        // Does preliminary checks, then calls doFlight to
        // generate flight stats
        generate_trip_info() {
            let plane = app.data.planner_plane_field
            let cities = app.data.flight_planner_items

            if (cities.length == 0) {
                app.data.planner_result = "Add some legs to your trip to see statistics!"
                return
            }

            // First, assert that the path connects properly
            let prevB = ""
            let validPath = true
            for (let city_set in cities) {
                if (city_set != 0) {
                    if (cities[city_set].city_A != prevB) {
                        validPath = false
                    }
                }
                prevB = cities[city_set].city_B
            }
            // If they don't have a valid path we stop here
            if (!validPath) {
                app.data.planner_result = "You entered an invalid path! Make sure all the cities connect up!"
                return
                // Else, generate a path list
            } else {
                var city_list = []
                for (let city_set in cities) {
                    city_list.push(cities[city_set].city_A)
                }
                city_list.push(cities.slice(-1)[0].city_B)
            }
            if (plane) {
                app.methods.doFlight(city_list, plane)
            } else {
                app.data.planner_result = "Choose a plane!"
            }

            return
        },

        // Calculates flight statistics given city path and plane
        doFlight(path, plane) {
            axios.get("/companion/planner_get_info", { params: { cities: path.join(','), plane: plane } }).then(function (response) {

                let cityObj = response.data.cityReturn
                let p = response.data.planeReturn
                let c = []
                for (let cityIndex in cityObj) {
                    let data = cityObj[cityIndex]
                    c[cityObj[cityIndex].city] = data
                }

                let originCity = path[0];
                let destCity = path.at(-1);

                // Find the raw distance between the origin and destination using the raw coordinates
                let rawDist = Math.floor(Math.sqrt(Math.pow(c[destCity].x - c[originCity].x, 2) + Math.pow(c[destCity].y - c[originCity].y, 2)));

                // Calculate the coin value, and the bonus for a full plane (if it has more than 1 cap)
                let coinValue = rawDist + 50;
                let coinValueBonus = coinValue;
                if (p.capacity > 1) {
                    coinValueBonus = Math.ceil(coinValue + (0.25 * coinValue));
                }


                // Calculate gain by multiplying the final coin value by the number of seats 
                let gain = coinValueBonus * p.capacity

                // Set the range, speed and weight to whatever the user requests.
                let range = p.range
                let speed = p.speed
                let weight = p.weight

                let totalRawDist = 0;
                let totalTimDist = 0;
                let counter = 0;
                let longestRawLegDist = 0;
                let longestTimDist = 0;
                let time = 0;

                // Calculate the total raw distance between all cities in the chain, and the longest leg
                while (counter <= path.length - 2) {
                    let rawLegDist = 0;
                    let timDist = 0;
                    if (path[counter] !== path[counter + 1]) {
                        let a = path[counter];
                        let b = path[counter + 1];

                        let timDistY = Math.floor(Math.abs(c[a].y - c[b].y))
                        let timDistX = Math.floor(Math.abs(c[a].x - c[b].x))

                        timDist = Math.floor(Math.abs(Math.sqrt((timDistX * timDistX) + (timDistY * timDistY))))

                        rawLegDist = Math.floor(Math.sqrt(Math.pow(c[b].x - c[a].x, 2) + Math.pow(c[b].y - c[a].y, 2)));

                        time += timDist / ((speed) / 700)
                    }
                    totalRawDist += rawLegDist;
                    totalTimDist += timDist

                    // Finds and records the longest leg of the journey
                    if (rawLegDist >= longestRawLegDist) {
                        longestRawLegDist = rawLegDist;
                    }
                    if (timDist >= longestTimDist) {
                        longestTimDist = timDist
                    }
                    counter += 1;
                }

                let loss = Math.floor((totalRawDist) * ((speed * weight * 100) / 40000));

                // Check if the plane is electric (array slot 7), if it is, we set loss to 0
                if (p.electric === true) {
                    loss = 0;
                }

                let profit = gain - loss
                let ft = Math.floor(time / 60)
                let profitPerHour = parseFloat((profit / (time / 60)) * 60).toFixed(2)

                app.data.planner_result = ''

                app.data.planner_result_profit = `${profit} coins (Gain = ${gain} | Loss = ${loss})`
                app.data.planner_result_flight_time = `${Math.floor(ft / 60)} hours and ${ft % 60} minutes`
                app.data.planner_result_profitph = `${profitPerHour} coins`
                app.data.planner_result_total_distance = `${totalRawDist * 4} miles`
                app.data.planner_result_longest_leg = `${longestRawLegDist * 4} miles`

                return [profit, totalRawDist * 4, longestRawLegDist * 4, range, speed, weight, time / 60, gain, loss];
            })
        },
    };

    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods,
    });

    app.init = () => {
        app.methods.get_entries()
        app.methods.get_curr_user_entry()
        app.methods.get_current_user()
        app.methods.generate_city_list()
        app.methods.get_flight_planner_entries()
    };

    app.init();
};

init(app);



