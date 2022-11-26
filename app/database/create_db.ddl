-- Create need tables for work app

create table if not exists comments(
    chat_id int4,
    comment text,
    date text,
    go_hospital text,
    id int4,
    quality int4
);

create table if not exists my_pet(
    id int4,
    telephone_number text,
    chat_id int4,
    pet_name text,
    pet_type text,
    pet_breed text,
    pet_birthday text,
    pet_gender text,
    pet_sterilized text,
    pet_vaccinated text,
    pet_last_date_vaccinated text,
    pet_chiped text,
    pet_number_chip text,
    last_clinic_name text
);

create table if not exists push_setting(
    id int4,
    after_minutte int4,
    type_comment text,
    comment_text text
);

create table if not exists send_push(
    chat_id int4,
    active int4,
    type_push text,
    when_push text
);

create table if not exists users(
    id int4,
    active int4,
    user_id int4
);

create table if not exists temprorary_data(
    chat_id int4,
    pet_name text,
    pet_type text,
    pet_breed text,
    pet_birthday text,
    pet_gender text,
    pet_sterilized text,
    pet_vaccinated text,
    pet_last_date_vaccinated text,
    pet_chiped text,
    pet_number_chip text
);

create table if not exists requests(
    req_id int4,
    user_id int4,
    user_nik varchar,
    user_telephone varchar,
    animal_age varchar,
    animal_breed varchar,
    animal_gender varchar,
    animal_type varchar,
    create_datetime timestamp,
    pet_sterilized text,
    pet_vaccinated text
);

create table if not exists requests_statuses(
    req_id int4,
    req_datetime timestamp,
    req_comment varchar,
    req_schedule_datetime timestamp,
    req_status varchar
);

