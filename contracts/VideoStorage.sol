pragma solidity ^0.8.0;

contract VideoStorage {
    mapping(string => bool) private videoHashes;

    function storeVideoHash(string memory hash) public {
        require(!videoHashes[hash], "Hash already exists.");
        videoHashes[hash] = true;
    }

    function checkVideoHash(string memory hash) public view returns (bool) {
        return videoHashes[hash];
    }
}