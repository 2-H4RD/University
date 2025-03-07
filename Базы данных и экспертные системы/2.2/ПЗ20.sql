select 2+2*2;

select sum(price)/sum(distance) from vehicle;

select price/5 as NDS from vehicle;

update vehicle set distance= distance+4;

select(2+5)<(2*3);

select * from vehicle where price <= 2000000;

select * from vehicle where distance <= 20000;

select gosn,(price/80.12) as usd_price from vehicle;

select gosn, round((price/80.12),2) as usd_price from vehicle;

select gosn, trunc((price/80.12),2) as usd_price from vehicle;

select sum(price) from vehicle;

select sum(price)/count(gosn) from vehicle;

select * from vehicle where price= (select max(price) from vehicle);

select * from vehicle where distance =(select min(distance)from vehicle);

select count(gosn) as total_cars from vehicle;

select count(distinct(model)) as registred_models from marka;

select count(producer) as producer_count from marka;

select * from vehicle limit 6;

select gosn,distance from vehicle order by distance asc;

select model from marka order by model asc;

select gosn,dateb,price,distance from vehicle order by price desc;

select gosn,dateb,price,distance from vehicle order by dateb asc;
