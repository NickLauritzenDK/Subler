#import <AppKit/AppKit.h>
#import <AVFoundation/AVFoundation.h>
#import <MP42Foundation/MP42Foundation.h>
// Exercise the actual embedded decoder without exporting a test hook.
@interface MP42AudioDecoder : NSObject
- (instancetype)initWithAudioFormat:(AudioStreamBasicDescription)format channelLayout:(AudioChannelLayout *)layout channelLayoutSize:(UInt32)size mixdownType:(MP42AudioMixdown)mix drc:(float)drc initialPadding:(UInt32)padding magicCookie:(NSData *)cookie error:(NSError **)error;
- (void)cancel;
@end
static int checkDecoderCookies(void) {
    const uint8_t config[]={0,0,16,0,0,16,40,10,14,2,0,255,0,0,0,0,0,0,0,0,0,0,172,68};
    const uint8_t prefix[]={0,0,0,36,'a','l','a','c',0,0,0,0};
    NSData *shortCookie=[NSData dataWithBytes:config length:sizeof(config)];
    NSMutableData *fullCookie=[NSMutableData dataWithBytes:prefix length:sizeof(prefix)];
    [fullCookie appendData:shortCookie];
    AudioStreamBasicDescription format={0};format.mFormatID=kAudioFormatAppleLossless;format.mSampleRate=44100;format.mChannelsPerFrame=2;
    AudioChannelLayout layout={0};layout.mChannelLayoutTag=kAudioChannelLayoutTag_Stereo;
    int failures=0;
    for (NSData *cookie in @[shortCookie,fullCookie,[shortCookie subdataWithRange:NSMakeRange(0,23)]]) {
        MP42AudioDecoder *decoder=[[MP42AudioDecoder alloc]initWithAudioFormat:format channelLayout:&layout channelLayoutSize:sizeof(layout) mixdownType:kMP42AudioMixdown_None drc:0 initialPadding:0 magicCookie:cookie error:nil];
        BOOL expected=cookie.length!=23;
        if ((decoder!=nil)!=expected) {fprintf(stderr,"FAIL: ALAC cookie %lu expected decoder %d\n",(unsigned long)cookie.length,expected);failures++;}
        else printf("PASS: ALAC cookie %lu\n",(unsigned long)cookie.length);
        [decoder cancel];
    }
    return failures?8:0;
}
static NSArray *inventory(NSArray *tracks) {
    NSMutableArray *result=[NSMutableArray array];
    for (MP42Track *t in tracks) if ([t isKindOfClass:MP42AudioTrack.class])
        [result addObject:@{@"channels":@(((MP42AudioTrack *)t).channels),@"timescale":@(t.timescale),@"duration_ms":@(t.duration),@"format":@(t.format)}];
    return result;
}
int main(int argc, const char **argv) { @autoreleasepool {
    if (argc==2 && !strcmp(argv[1],"--decoder-cookies")) return checkDecoderCookies();
    if (argc==4 && !strcmp(argv[1],"--timeline")) {
        AVURLAsset *asset=[AVURLAsset URLAssetWithURL:[NSURL fileURLWithPath:@(argv[2])] options:nil];
        AVAssetTrack *track=[[asset tracksWithMediaType:AVMediaTypeAudio]firstObject];
        if (!track) return 12;
        NSMutableArray *segments=[NSMutableArray array];
        for (AVAssetTrackSegment *segment in track.segments) {
            CMTimeMapping map=segment.timeMapping;
            [segments addObject:@{@"empty":@(segment.isEmpty),@"start":@(CMTimeGetSeconds(map.target.start)),@"duration":@(CMTimeGetSeconds(map.target.duration)),@"source_start":segment.isEmpty?[NSNull null]:@(CMTimeGetSeconds(map.source.start))}];
        }
        NSData *data=[NSJSONSerialization dataWithJSONObject:segments options:NSJSONWritingPrettyPrinted error:nil];
        return [data writeToFile:@(argv[3]) atomically:YES]?0:13;
    }
    if (argc==5 && !strcmp(argv[1],"--make-offset")) {
        NSError *error=nil;
        NSURL *url=[NSURL fileURLWithPath:@(argv[3])];
        if (![[NSFileManager defaultManager]copyItemAtPath:@(argv[2]) toPath:@(argv[3]) error:&error]) return 9;
        MP42File *source=[[MP42File alloc]initWithURL:url error:&error];
        if (!source) return 10;
        for (MP42Track *track in source.tracks) if ([track isKindOfClass:MP42AudioTrack.class]) track.startOffset=atof(argv[4]);
        return [source updateMP4FileWithOptions:@{} error:&error]?0:11;
    }
    if (argc != 4) return 2;
    NSError *error=nil;
    MP42FileImporter *importer=[[MP42FileImporter alloc] initWithURL:[NSURL fileURLWithPath:@(argv[1])] error:&error];
    if (!importer) { NSLog(@"Import: %@",error); return 3; }
    NSArray *before=inventory(importer.tracks);
    MP42File *file=[[MP42File alloc] init];
    for (MP42Track *t in importer.tracks) if ([t isKindOfClass:MP42AudioTrack.class]) {
        t.conversionSettings=[MP42AudioConversionSettings audioConversionWithBitRate:160 mixDown:strcmp(argv[3],"stereo")==0?kMP42AudioMixdown_Stereo:kMP42AudioMixdown_None drc:0];
        [file addTrack:t];
    }
    for (MP42Track *t in importer.tracks) NSLog(@"Input codec %u cookie bytes %lu", (unsigned)t.format, (unsigned long)[importer magicCookieForTrack:t].length);
    NSURL *out=[NSURL fileURLWithPath:@(argv[2])];
    if (![file writeToUrl:out options:@{} error:&error]) { NSLog(@"Write: %@",error); return 4; }
    MP42File *read=[[MP42File alloc] initWithURL:out error:&error];
    if (!read) { NSLog(@"Read: %@",error); return 5; }
    NSData *json=[NSJSONSerialization dataWithJSONObject:@{@"input":before,@"output":inventory(read.tracks)} options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:&error];
    return [json writeToFile:[@(argv[2]) stringByAppendingString:@".json"] atomically:YES]?0:6;
} }
