CREATE TABLE "train_arrival_train_duration" (
  "train arrival id" INTEGER,
  "train duration id" INTEGER,
  PRIMARY KEY ("train arrival id")
);

CREATE TABLE "train_arrival_train_price" (
  "train arrival id" INTEGER,
  "train price id" INTEGER,
  PRIMARY KEY ("train arrival id")
);

CREATE TABLE "train_arrival_train_details" (
  "train arrival id" INTEGER,
  "train details id" INTEGER,
  PRIMARY KEY ("train arrival id")
);

CREATE TABLE "train_booking_reference_train_arrival" (
  "train booking reference id" INTEGER,
  "train arrival id" INTEGER,
  PRIMARY KEY ("train booking reference id")
);

CREATE TABLE "train_details_train_arrival" (
  "train details id" INTEGER,
  "train arrival id" INTEGER,
  PRIMARY KEY ("train details id")
);

CREATE TABLE "train_arrival" (
  "train arrival id" INTEGER,
  "arrival time" TIME,
  "day of the train" TEXT,
  "departure location" TEXT,
  "destination" TEXT,
  "leaving time" TIME,
  "day of the hotel booking" TEXT,
  "day of the restaurant booking" TEXT,
  "Restaurant requested time" TIME,
  PRIMARY KEY ("train arrival id"),
  FOREIGN KEY ("train arrival id") REFERENCES "train_arrival_train_duration" ("train arrival id"),
  FOREIGN KEY ("train arrival id") REFERENCES "train_arrival_train_price" ("train arrival id"),
  FOREIGN KEY ("train arrival id") REFERENCES "train_arrival_train_details" ("train arrival id"),
  FOREIGN KEY ("train arrival id") REFERENCES "train_booking_reference_train_arrival" ("train arrival id"),
  FOREIGN KEY ("train arrival id") REFERENCES "train_details_train_arrival" ("train arrival id")
);

CREATE TABLE "train_booking_reference" (
  "train booking reference id" INTEGER,
  "reference number" INTEGER,
  PRIMARY KEY ("train booking reference id"),
  FOREIGN KEY ("train booking reference id") REFERENCES "train_booking_reference_train_arrival" ("train booking reference id")
);

CREATE TABLE "train_duration" (
  "train duration id" INTEGER,
  "duration" INTERVAL,
  PRIMARY KEY ("train duration id"),
  FOREIGN KEY ("train duration id") REFERENCES "train_arrival_train_duration" ("train duration id")
);

CREATE TABLE "train_price" (
  "train price id" INTEGER,
  "price" NUMERIC(10, 2),
  PRIMARY KEY ("train price id"),
  FOREIGN KEY ("train price id") REFERENCES "train_arrival_train_price" ("train price id")
);

CREATE TABLE "train_details_train_price" (
  "train details id" INTEGER,
  "train price id" INTEGER,
  PRIMARY KEY ("train details id")
);

CREATE TABLE "train_details_train_duration" (
  "train details id" INTEGER,
  "train duration id" INTEGER,
  PRIMARY KEY ("train details id")
);

CREATE TABLE "train_details_train_booking_reference" (
  "train details id" INTEGER,
  "train booking reference id" INTEGER,
  PRIMARY KEY ("train details id")
);

CREATE TABLE "train_details" (
  "train details id" INTEGER,
  "number of train tickets needed" INTEGER,
  "id of the train" INTEGER,
  "Hotel requested people" INTEGER,
  "Hotel requested stay" INTEGER,
  "Restaurant requested people" INTEGER,
  PRIMARY KEY ("train details id"),
  FOREIGN KEY ("train details id") REFERENCES "train_details_train_arrival" ("train details id"),
  FOREIGN KEY ("train details id") REFERENCES "train_details_train_price" ("train details id"),
  FOREIGN KEY ("train details id") REFERENCES "train_details_train_duration" ("train details id"),
  FOREIGN KEY ("train details id") REFERENCES "train_details_train_booking_reference" ("train details id")
);

CREATE TABLE "hotel_booking_reference_hotel_details" (
  "hotel booking reference id" INTEGER,
  "hotel details id" INTEGER,
  PRIMARY KEY ("hotel booking reference id")
);

CREATE TABLE "hotel_details_hotel_booking_reference" (
  "hotel details id" INTEGER,
  "hotel booking reference id" INTEGER,
  PRIMARY KEY ("hotel details id")
);

CREATE TABLE "hotel_details" (
  "hotel details id" INTEGER,
  "address" TEXT,
  "area" TEXT,
  "name" TEXT,
  "phone number" TEXT,
  "price budget" TEXT,
  "star rating" INTEGER,
  "type" TEXT,
  PRIMARY KEY ("hotel details id"),
  FOREIGN KEY ("hotel details id") REFERENCES "hotel_booking_reference_hotel_details" ("hotel details id"),
  FOREIGN KEY ("hotel details id") REFERENCES "hotel_details_hotel_booking_reference" ("hotel details id")
);

CREATE TABLE "hotel_booking_reference" (
  "hotel booking reference id" INTEGER,
  "reference number" INTEGER,
  "postal code" TEXT,
  PRIMARY KEY ("hotel booking reference id"),
  FOREIGN KEY ("hotel booking reference id") REFERENCES "hotel_booking_reference_hotel_details" ("hotel booking reference id")
);

CREATE TABLE "restaurant_booking_reference_restaurant_details" (
  "restaurant booking reference id" INTEGER,
  "restaurant details id" INTEGER,
  PRIMARY KEY ("restaurant booking reference id")
);

CREATE TABLE "restaurant_details_restaurant_booking_reference" (
  "restaurant details id" INTEGER,
  "restaurant booking reference id" INTEGER,
  PRIMARY KEY ("restaurant details id")
);

CREATE TABLE "restaurant_details" (
  "restaurant details id" INTEGER,
  "address" TEXT,
  "area" TEXT,
  "cuisine" TEXT,
  "name" TEXT,
  "phone number" TEXT,
  "postal code" TEXT,
  "price budget" TEXT,
  PRIMARY KEY ("restaurant details id"),
  FOREIGN KEY ("restaurant details id") REFERENCES "restaurant_booking_reference_restaurant_details" ("restaurant details id"),
  FOREIGN KEY ("restaurant details id") REFERENCES "restaurant_details_restaurant_booking_reference" ("restaurant details id")
);

CREATE TABLE "restaurant_booking_reference" (
  "restaurant booking reference id" INTEGER,
  "reference number" INTEGER,
  PRIMARY KEY ("restaurant booking reference id"),
  FOREIGN KEY ("restaurant booking reference id") REFERENCES "restaurant_booking_reference_restaurant_details" ("restaurant booking reference id")
);
