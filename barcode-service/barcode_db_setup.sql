create schema barcode;

create table products
(
    id        serial
        constraint id
            primary key,
    name      varchar,
    producer  varchar,
    material  varchar,
    barcode   varchar not null,
    part_name varchar,
    detail    varchar,
    material_code varchar
);