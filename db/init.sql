CREATE TABLE country
(
    id_cntry integer PRIMARY KEY,
    cntry_name varchar(50) CHECK (cntry_name <> '')
);


CREATE TABLE information
(
    dte date,
    id_cntry integer REFERENCES country(id_cntry) ON DELETE CASCADE ON UPDATE CASCADE,
    temperature real CHECK (temperature >= -273),
    new_cases integer CHECK (new_cases >= 0),
    PRIMARY KEY (dte, id_cntry)
);


CREATE TABLE avg_year_info
(
    dte_year integer CHECK (dte_year > 2019),
    id_cntry integer REFERENCES country(id_cntry) ON DELETE CASCADE ON UPDATE CASCADE,
    avg_year_temp real CHECK (avg_year_temp >= -273),
    avg_year_cases integer CHECK (avg_year_cases >= 0),
    PRIMARY KEY (dte_year, id_cntry)
);


CREATE TABLE ai_models
(
    id_cntry integer REFERENCES country(id_cntry) ON DELETE CASCADE ON UPDATE CASCADE,
    model_name varchar(20) CHECK (model_name <> ''),
    model_file BYTEA,
    dte date
    PRIMARY KEY (id_cntry, model_name)
);