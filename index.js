
const scooterListSendToTelegramBroken = async () => {



    // array = [49039988, 48371734, 48429880, 46655497]
    array = [49039988]
    // 295


    for (let index = 0; index < array.length; index++) {
        // const element = array[index];

        const responseListGeoRIC = await fetch(`https://api.partner.market.yandex.ru/v2/campaigns/${array[index]}/orders.json?page=2`, {
            method: 'GET',
            headers: {
                'Authorization': 'OAuth oauth_token="///", oauth_client_id="///"',
                'Content-Type': 'application/json'
            },
        })
        // .then((response) => {
        //     return response.json();
        // })
        // .then((data) => {
        //     console.log(data);
        // });
        const responseListGeoRICData = await responseListGeoRIC.json()
        console.log('DATATA: ', responseListGeoRICData)
        // console.log('DATATA: ', responseListGeoRICData.orders[1])



        // console.log('DATATA: ', JSON.stringify(responseListGeoRICData))


        // let data2 = await JSON.parse(responseListGeoRIC)
        // console.log(data2);

        // console.log("Всего: " + responseListGeoRIC);

        // const responseListGeoRICData = await responseListGeoRIC.json()
        // console.log("Всего: " + responseListGeoRICData);


    }



    // var myHeaders = new Headers();
    // myHeaders.append('Authorization', 'OAuth oauth_token="8327eb0a74844851ba0b86bc3d28f889", oauth_client_id="e765efd50206404b83e442e5f3a41fc6"');

    // var requestOptions = {
    //     method: 'GET',
    //     headers: myHeaders,
    //     redirect: 'follow'
    // };

    // fetch(`https://api.partner.market.yandex.ru/v2/campaigns/48429880/stats/orders`, requestOptions)
    //     // .then(response => response.text())
    //     .then(response => {
    //         console.log(response.status);       // 200
    //         console.log(response.statusText);   // OK
    //         console.log(response.url);          // http://localhost:3000/hello
    //     })
    // .then(result => console.log(result))
    // .catch(error => console.log('error', error));

    // }


}