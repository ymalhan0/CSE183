let app = {};

let init = (app) => {
    app.data = {
        offers: [],
        reservations: [],
    };

    app.enumerate = (a) => {
        let k = 0;
        a.map((e) => { e._idx = k++; });
        return a;
    };

    app.methods = {
        get_offers_reservations: async () => {
            let res = await axios.get("/companion/get_offers_reservations");
            app.vue.offers = app.enumerate(res.data.offers);
            app.vue.reservations = app.enumerate(res.data.reservations);
        },
        
        complete_trade(id) {
            axios.post("/companion/complete_offer", { id: id }).then(function (response) {
                app.methods.get_offers_reservations();
            });
        },
        
        decline_trade(id) {
            axios.post("/companion/decline_trade", { id: id }).then(function (response) {
                app.methods.get_offers_reservations();
            });
        },

        unreserve_trade(id) {
            axios.post("/companion/unreserve_trade", { id: id }).then(function (response) {
                app.methods.get_offers_reservations();
            });
        },
    };

    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods,
    });

    app.methods.get_offers_reservations();
};

init(app);
