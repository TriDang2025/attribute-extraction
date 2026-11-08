CREATE TABLE "hotel" (
  "id" INTEGER,
  "name" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "stars" INTEGER,
  "price_range" TEXT,
  "free_wifi" BOOLEAN,
  "free_parking" BOOLEAN,
  "area" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "restaurant" (
  "id" INTEGER,
  "name" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "price_range" TEXT,
  "cuisine" TEXT,
  "area" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "attraction" (
  "id" INTEGER,
  "name" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "entrance_fee" NUMERIC(10, 2),
  "type" TEXT,
  "area" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "train" (
  "id" INTEGER,
  "train_id" TEXT,
  "departure_station" TEXT,
  "arrival_station" TEXT,
  "departure_time" TIME,
  "arrival_time" TIME,
  "travel_date" DATE,
  "price" NUMERIC(10, 2),
  "travel_time" INTERVAL,
  PRIMARY KEY ("id")
);

CREATE TABLE "reservation" (
  "id" INTEGER,
  "reference_number" TEXT,
  "reservation_type" TEXT,
  "date" DATE,
  "time" TIME,
  "people" INTEGER,
  "hotel_id" INTEGER,
  "restaurant_id" INTEGER,
  "train_id" INTEGER,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("hotel_id") REFERENCES "hotel" ("id"),
  FOREIGN KEY ("restaurant_id") REFERENCES "restaurant" ("id"),
  FOREIGN KEY ("train_id") REFERENCES "train" ("id")
);

CREATE TABLE "taxi" (
  "id" INTEGER,
  "reference_number" TEXT,
  "departure_location" TEXT,
  "arrival_location" TEXT,
  "departure_time" TIME,
  "arrival_time" TIME,
  "car_type" TEXT,
  "contact_number" TEXT,
  PRIMARY KEY ("id")
);
