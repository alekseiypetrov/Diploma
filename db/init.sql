CREATE TABLE country
(
    id_cntry integer PRIMARY KEY,
    cntry_name varchar(30) CHECK (NOT cntry_name='')
);


CREATE TABLE information
(
    dte date,
    id_cntry integer REFERENCES country(id_cntry) ON DELETE CASCADE ON UPDATE CASCADE,
    temperature real CHECK (temperature >= -273),
    new_cases integer CHECK (new_cases >= 0),
    PRIMARY KEY (dte, id_cntry)
);
