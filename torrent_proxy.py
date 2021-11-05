import os.path
import bencodepy
import cefpyco


class Peer:

    @staticmethod
    def join_file(fileList, filePath):

        with open(filePath, "wb") as saveFile:
            for f in fileList:
                data = open(f, "rb").read()
                saveFile.write(data)
                saveFile.flush()


class Seed:
    @staticmethod
    def divide_file(filePath, chunkSize):

        readDataSize = 0
        fileList = []
        i = 0

        f = open(filePath, "rb")
        contentLength = os.path.getsize(filePath)

        while readDataSize < contentLength:

            f.seek(readDataSize)

            data = f.read(chunkSize)

            saveDirectory = filePath + ".dir"
            os.makedirs(saveDirectory, exist_ok=True)
            saveFilePath = saveDirectory + "/" + filePath + "." + str(i)
            with open(saveFilePath, "wb") as saveFile:
                saveFile.write(data)

            readDataSize += len(data)
            i += 1
            fileList.append(saveFilePath)

        return fileList


if __name__ == '__main__':
    seed = Seed()
    peer = Peer()

    torrent_file = open("ubuntu-20.04.3-desktop-amd64.iso.torrent", "rb").read()
    decodedFile = bencodepy.decode(torrent_file)
    print(decodedFile)

    fileList = seed.divide_file("testPicture.jpg", 1024)
    peer.join_file(fileList, "join_testPicture.jpg")
