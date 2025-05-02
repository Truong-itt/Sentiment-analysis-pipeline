## MongoDB Replica Set Initialization & Test Data

### Start MongoDB Services
```bash
docker-compose up -d
```

### Configure Replica Set & Initialize Data
1. Access primary MongoDB container:
   ```bash
   docker exec -it mongo1 mongosh
   ```
2. Initialize Replica Set:
   ```javascript
   rs.initiate({_id: "rs0", members: [{_id: 0, host: "mongo1:27017"}, {_id: 1, host: "mongo2:27018"}, {_id: 2, host: "mongo3:27019"}]});
   ```
3. Create user:
   ```javascript
   db.createUser({user: "rotoro", pwd: "rotoro123", roles: [{role: "read", db: "rotoro"}, {role: "readWrite", db: "rotoro"}, {role: "clusterMonitor", db: "admin"}, {role: "readAnyDatabase", db: "admin"}]});
   ```
4. Insert test data:
   ```javascript
   use rotoro; db.giaitri.insertOne({name: "Sample Item", price: 100, stock: 50}); db.kinhdoanh.insertOne({name: "Sample Item", price: 100, stock: 50}); db.tintucmoi.insertOne({name: "Sample Item", price: 100, stock: 50});
   ```
5. Verify:
   ```javascript
   show collections; db.giaitri.find().pretty()
   ```