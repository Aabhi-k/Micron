FROM openjdk:17-jdk-slim

WORKDIR /app

COPY target/passman.jar app.jar

COPY env.properties env.properties

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]