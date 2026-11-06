CREATE TABLE "attraction" (
  "attraction_id" INTEGER,
  "name" TEXT,
  "type" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "entrance_fee" REAL,
  PRIMARY KEY ("attraction_id")
);

CREATE TABLE "restaurant" (
  "restaurant_id" INTEGER,
  "name" TEXT,
  "type" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "phone_number" TEXT,
  "price_range" TEXT,
  PRIMARY KEY ("restaurant_id")
);

CREATE TABLE "hotel" (
  "hotel_id" INTEGER,
  "name" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "price_range" TEXT,
  "stars" INTEGER,
  "free_wifi" BOOLEAN,
  "free_parking" BOOLEAN,
  PRIMARY KEY ("hotel_id")
);

CREATE TABLE "train" (
  "train_id" INTEGER,
  "train_number" TEXT,
  "departure_station" TEXT,
  "arrival_station" TEXT,
  "departure_time" TIME,
  "arrival_time" TIME,
  "travel_date" DATE,
  "price_per_ticket" REAL,
  "reference_number" TEXT,
  PRIMARY KEY ("train_id")
);

CREATE TABLE "reservation" (
  "reservation_id" INTEGER,
  "attraction_id" INTEGER,
  "restaurant_id" INTEGER,
  "hotel_id" INTEGER,
  "reservation_date" DATE,
  "reservation_time" TIME,
  "number_of_people" INTEGER,
  "reference_number" TEXT,
  PRIMARY KEY ("reservation_id"),
  FOREIGN KEY ("attraction_id") REFERENCES "attraction" ("attraction_id"),
  FOREIGN KEY ("restaurant_id") REFERENCES "restaurant" ("restaurant_id"),
  FOREIGN KEY ("hotel_id") REFERENCES "hotel" ("hotel_id")
);

CREATE TABLE "taxi" (
  "taxi_id" INTEGER,
  "pickup_location" TEXT,
  "dropoff_location" TEXT,
  "pickup_time" TIME,
  "contact_number" TEXT,
  "car_type" TEXT,
  "reference_number" TEXT,
  PRIMARY KEY ("taxi_id")
);
